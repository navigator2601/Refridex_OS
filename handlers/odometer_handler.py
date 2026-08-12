# handlers/odometer_handler.py

import logging
import os
import re
import warnings
from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

# --- Приглушуємо специфічне попередження від PyTorch ---
# Це попередження з'являється при використанні CPU, оскільки pin_memory=True корисне тільки для GPU.
# Воно не впливає на роботу, але засмічує логи.
warnings.filterwarnings(
    "ignore", category=UserWarning, message=".*'pin_memory' argument is set as true.*"
)

# Імпортуємо необхідні бібліотеки для розпізнавання
# Переконайтесь, що вони встановлені: pip install ultralytics easyocr opencv-python-headless
try:
    from ultralytics import YOLO
    import easyocr
    import cv2
    MODELS_LOADED = True
except ImportError:
    MODELS_LOADED = False
    logging.getLogger(__name__).critical("Не вдалося імпортувати бібліотеки для розпізнавання (ultralytics, easyocr, cv2). Функціонал пробігу буде недоступний.")

from common.states import OdometerStates
from keyboards.inline_keyboard import get_odometer_confirmation_keyboard
from telegram_client_module.telethon_client import TelethonClientManager

logger = logging.getLogger(__name__)
router = Router()

# --- Ініціалізація моделей ---
# Ініціалізуємо моделі один раз при старті, якщо бібліотеки завантажено
if MODELS_LOADED:
    # РЕКОМЕНДАЦІЯ: Перейменуйте ваш файл 'best.pt' на 'odometer_detector.pt' для ясності
    ODOMETER_MODEL_PATH = './models/odometer_detector.pt'
    if os.path.exists(ODOMETER_MODEL_PATH):
        yolo_model = YOLO(ODOMETER_MODEL_PATH)
        ocr_reader = easyocr.Reader(['en'], gpu=False) # gpu=False для серверів без GPU
        logger.info("Моделі YOLO та EasyOCR для розпізнавання пробігу успішно завантажено.")
    else:
        MODELS_LOADED = False
        logger.error(f"Файл моделі не знайдено за шляхом: {ODOMETER_MODEL_PATH}. Функціонал пробігу буде недоступний.")

def process_odometer(image_path: str) -> tuple[str | None, object | None]:
    """
    Обробляє зображення для розпізнавання пробігу за допомогою YOLO та EasyOCR.
    """
    if not MODELS_LOADED:
        logger.error("Спроба викликати process_odometer, але моделі не завантажені.")
        return None, None

    try:
        # 1. Використати yolo_model для знаходження області з одометром
        results = yolo_model(image_path, verbose=False)

        if not results or not results[0].boxes:
            logger.warning(f"YOLO не знайшла об'єктів на зображенні: {image_path}")
            return None, None

        # Беремо перший знайдений об'єкт з найбільшою впевненістю
        box = results[0].boxes[0]
        coords = box.xyxy[0].cpu().numpy().astype(int)
        confidence = box.conf[0].cpu().numpy()

        logger.info(f"YOLO знайшла одометр з впевненістю {confidence:.2f} за координатами {coords}")

        # Встановлюємо поріг впевненості, наприклад, 50%
        if confidence < 0.50:
            logger.warning(f"Впевненість {confidence:.2f} нижча за поріг 0.50. Результат відхилено.")
            return None, None

        # 2. Обрізаємо зображення (crop_img)
        img = cv2.imread(image_path)
        x1, y1, x2, y2 = coords
        crop_img = img[y1:y2, x1:x2]

        # 3. Використати ocr_reader для розпізнавання цифр
        ocr_result = ocr_reader.readtext(crop_img, allowlist='0123456789')

        if not ocr_result:
            logger.warning("EasyOCR не розпізнав текст на обрізаному зображенні.")
            return None, None

        # 4. Очищуємо результат, залишаючи тільки цифри
        recognized_text = "".join([res[1] for res in ocr_result])
        digits = re.sub(r'\D', '', recognized_text)

        logger.info(f"EasyOCR розпізнав текст: '{recognized_text}', очищені цифри: '{digits}'")
        return digits, crop_img
    except Exception as e:
        logger.error(f"Помилка в process_odometer: {e}", exc_info=True)
        return None, None

@router.message(F.text == "Пробіг")
async def prompt_for_odometer_photo(message: types.Message, state: FSMContext):
    if not MODELS_LOADED:
        await message.reply("Вибачте, сервіс розпізнавання пробігу тимчасово недоступний через технічні проблеми.")
        return
        
    await message.reply("Будь ласка, надішліть фотографію одометра.")
    await state.set_state(OdometerStates.waiting_for_photo)

@router.message(OdometerStates.waiting_for_photo, F.photo)
async def handle_odometer_photo(message: types.Message, state: FSMContext, bot: Bot):
    # 1. Повідомляємо користувача про початок обробки
    processing_message = await message.reply("⏳ Розпізнаю пробіг... Це може зайняти декілька секунд.")

    # 2. Зберігаємо фото від користувача
    photo_path = f"temp_{message.from_user.id}.jpg"
    digits = None

    try:
        await bot.download(message.photo[-1], destination=photo_path)
        
        # 3. Проганяємо через нашу функцію process_odometer
        digits, crop_img = process_odometer(photo_path)
    finally:
        # 4. Гарантовано видаляємо тимчасовий файл
        if os.path.exists(photo_path):
            os.remove(photo_path)

    # 5. Видаляємо повідомлення "Розпізнаю..."
    await processing_message.delete()

    # 6. Пропонуємо підтвердити та відправити результат
    if digits:
        await state.update_data(odometer_reading=digits)
        await state.set_state(OdometerStates.waiting_for_confirmation)
        await message.answer(
            f"✅ Пробіг розпізнано: <b>{digits} км</b>.\n\nНадіслати звіт у робочий чат?",
            reply_markup=get_odometer_confirmation_keyboard()
        )
    else:
        await message.answer("❌ Не вдалося чітко зчитати покази одометра. Будь ласка, зробіть чіткіше фото.")
        # Стан не скидаємо, щоб користувач міг надіслати інше фото

@router.callback_query(OdometerStates.waiting_for_confirmation, F.data == "send_odometer_report")
async def send_odometer_report(callback: types.CallbackQuery, state: FSMContext, telethon_manager: TelethonClientManager):
    data = await state.get_data()
    digits = data.get("odometer_reading")
    user = callback.from_user

    # ID робочого чату (потрібно вказати в .env)
    WORK_CHAT_ID = int(os.getenv("WORK_CHAT_ID", "0"))
    if WORK_CHAT_ID == 0:
        await callback.answer("Помилка: не налаштовано ID робочого чату.", show_alert=True)
        return

    report_text = f"🚗 Водій {user.full_name} (@{user.username}) зафіксував пробіг: <b>{digits} км</b>."
    
    # Логіка відправки через Telethon
    main_client = telethon_manager.get_client(os.getenv("TELEGRAM_PHONE"))
    if main_client and await main_client.is_user_authorized():
        await main_client.send_message(WORK_CHAT_ID, report_text, parse_mode='html')
        await callback.message.edit_text(f"✅ Звіт про пробіг (<b>{digits} км</b>) успішно надіслано.")
    else:
        await callback.message.edit_text("❌ Помилка: API-зв'язок не авторизований. Неможливо надіслати звіт.")
    
    await state.clear()
    await callback.answer()

@router.callback_query(OdometerStates.waiting_for_confirmation, F.data == "cancel_odometer_report")
async def cancel_odometer_report(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Дію скасовано.")
    await state.clear()
    await callback.answer()