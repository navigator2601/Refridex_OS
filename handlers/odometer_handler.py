# handlers/odometer_handler.py

import logging
import os
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

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
    Обробляє зображення для розпізнавання пробігу.
    Це ваша функція, яку потрібно буде реалізувати.
    """
    # Тут має бути ваша логіка з використанням yolo_model та ocr_reader
    # 1. Використати yolo_model для знаходження області з одометром на фото.
    # 2. Обрізати зображення (crop_img).
    # 3. Використати ocr_reader для розпізнавання цифр на обрізаному зображенні.
    # 4. Повернути розпізнані цифри та, за бажанням, обрізане зображення для дебагу.
    
    # Поки що це заглушка
    logger.warning("Функція process_odometer ще не реалізована. Повертається тестовий результат.")
    return "123456", None # Повертаємо тестові дані

@router.message(F.text == "Пробіг")
async def prompt_for_odometer_photo(message: types.Message, state: FSMContext):
    if not MODELS_LOADED:
        await message.reply("Вибачте, сервіс розпізнавання пробігу тимчасово недоступний через технічні проблеми.")
        return
        
    await message.reply("Будь ласка, надішліть фотографію одометра.")
    await state.set_state(OdometerStates.waiting_for_photo)

@router.message(OdometerStates.waiting_for_photo, F.photo)
async def handle_odometer_photo(message: types.Message, state: FSMContext):
    # 1. Зберігаємо фото від користувача
    photo_path = f"temp_{message.from_user.id}.jpg"
    await message.photo[-1].download(destination_file=photo_path)
    
    # 2. Проганяємо через нашу функцію process_odometer
    digits, crop_img = process_odometer(photo_path)
    
    # 3. Видаляємо тимчасовий файл
    if os.path.exists(photo_path):
        os.remove(photo_path)
        
    # 4. Відправляємо результат водію
    if digits:
        await message.reply(f"✅ Пробіг зафіксовано: <b>{digits} км</b>")
    else:
        await message.reply("❌ Не вдалося чітко зчитати покази одометра. Будь ласка, зробіть чіткіше фото.")
    
    await state.clear()