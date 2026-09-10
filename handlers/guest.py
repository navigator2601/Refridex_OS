# handlers/guest.py
import re
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from config import config
from database.models.user import UserModel, AccessLevel
from database.repositories.auth_repo import AuthRepository
from keyboards.reply_keyboard import (
    get_main_reply_keyboard,
    get_contact_request_keyboard,
    get_cancel_keyboard,
)
from keyboards.inline_keyboard import get_user_approval_keyboard

logger = logging.getLogger(__name__)

router = Router(name="guest_router")


class GuestRegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()
    waiting_for_call_sign = State()


# ---------------------------------------------------------------------------
# Скасування процесу реєстрації
# ---------------------------------------------------------------------------
@router.message(F.text == "❌ Скасувати")
async def cancel_registration(message: Message, state: FSMContext, user: Optional[UserModel]) -> None:
    """Скидання поточного стану FSM та повернення до головного меню."""
    await state.clear()
    access_level = user.access_level if user else AccessLevel.GUEST
    await message.answer(
        "❌ Дію скасовано. Повернення до головного меню.",
        reply_markup=get_main_reply_keyboard(access_level=access_level),
    )


# ---------------------------------------------------------------------------
# Початок подання заявки
# ---------------------------------------------------------------------------
@router.message(F.text == "📝 Подати заявку на реєстрацію")
async def start_registration(message: Message, state: FSMContext, user: Optional[UserModel]) -> None:
    """Початок анкети реєстрації для отримання ролі Монтажника."""
    # Якщо користувач вже авторизований (Монтажник або вище), не починаємо анкету
    if user and user.access_level >= AccessLevel.USER:
        await message.answer(
            f"✅ Ви вже авторизовані в системі як <b>{user.access_level.badge}</b>.",
            reply_markup=get_main_reply_keyboard(access_level=user.access_level),
            parse_mode="HTML",
        )
        return

    await state.set_state(GuestRegistrationStates.waiting_for_phone)
    text = (
        "📝 <b>Реєстрація монтажника (Крок 1 з 3)</b>\n\n"
        "Будь ласка, надішліть ваш контакт за допомогою кнопки <b>«📱 Поділитися контактом»</b> "
        "нижче або введіть номер телефону вручну (у форматі <code>+380XXXXXXXXX</code>):"
    )
    await message.answer(
        text=text,
        reply_markup=get_contact_request_keyboard(),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Крок 1: Обробка номера телефону
# ---------------------------------------------------------------------------
@router.message(GuestRegistrationStates.waiting_for_phone, F.contact)
@router.message(GuestRegistrationStates.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = None
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = f"+{phone}"
    elif message.text:
        raw_phone = re.sub(r"[^\d+]", "", message.text.strip())
        if re.match(r"^\+?\d{10,15}$", raw_phone):
            phone = raw_phone if raw_phone.startswith("+") else f"+{raw_phone}"

    if not phone:
        await message.answer(
            "⚠️ Некоректний формат номера телефону.\n"
            "Скористайтеся кнопкою <b>«📱 Поділитися контактом»</b> або введіть номер у форматі: <code>+380XXXXXXXXX</code>",
            reply_markup=get_contact_request_keyboard(),
            parse_mode="HTML",
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(GuestRegistrationStates.waiting_for_name)

    text = (
        f"✅ Номер телефону зафіксовано: <code>{phone}</code>\n\n"
        "👤 <b>Крок 2 з 3: Ваше офіційне ПІБ</b>\n\n"
        "Введіть ваше Прізвище, Ім'я та По батькові (наприклад: <i>Шевченко Тарас Григорович</i>):"
    )
    await message.answer(text=text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


# ---------------------------------------------------------------------------
# Крок 2: Обробка ПІБ
# ---------------------------------------------------------------------------
@router.message(GuestRegistrationStates.waiting_for_name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()
    parts = full_name.split()

    if len(parts) < 2 or len(full_name) < 4:
        await message.answer(
            "⚠️ Будь ласка, введіть принаймні Прізвище та Ім'я (наприклад: <i>Шевченко Тарас</i>):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    surname = parts[0]
    official_name = parts[1]
    patronymic = parts[2] if len(parts) > 2 else None

    await state.update_data(surname=surname, official_name=official_name, patronymic=patronymic)
    await state.set_state(GuestRegistrationStates.waiting_for_call_sign)

    text = (
        f"✅ ПІБ зафіксовано: <b>{surname} {official_name}</b>\n\n"
        "🏷️ <b>Крок 3 з 3: Робочий позивний</b>\n\n"
        "Введіть бажаний позивний або номер бригади (наприклад: <code>ІМ-5</code>, <code>БР-2</code>):"
    )
    await message.answer(text=text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


# ---------------------------------------------------------------------------
# Крок 3: Обробка позивного та збереження в БД
# ---------------------------------------------------------------------------
@router.message(GuestRegistrationStates.waiting_for_call_sign, F.text)
async def process_call_sign(
    message: Message,
    state: FSMContext,
    auth_repo: Optional[AuthRepository],
) -> None:
    call_sign = message.text.strip().upper()
    if len(call_sign) < 2 or len(call_sign) > 20:
        await message.answer(
            "⚠️ Позивний повинен містити від 2 до 20 символів (наприклад: <code>ІМ-5</code>):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    phone = data.get("phone")
    surname = data.get("surname")
    official_name = data.get("official_name")
    patronymic = data.get("patronymic")

    # Зберігаємо в базі даних
    if auth_repo:
        try:
            await auth_repo.update_profile(
                user_id=message.from_user.id,
                call_sign=call_sign,
                phone=phone,
                surname=surname,
                official_name=official_name,
                patronymic=patronymic,
            )
        except Exception as e:
            logger.error(f"Помилка оновлення профілю користувача {message.from_user.id}: {e}")

    await state.clear()

    user_text = (
        "🎉 <b>Заявку успішно надіслано!</b>\n\n"
        f"<b>Телефон:</b> <code>{phone}</code>\n"
        f"<b>ПІБ:</b> {surname} {official_name} {patronymic or ''}\n"
        f"<b>Позивний:</b> <code>{call_sign}</code>\n\n"
        "⏳ Вашу анкету передано адміністратору на перевірку. "
        "Щойно доступ буде підтверджено, ви отримаєте повідомлення, а меню автоматично розшириться.\n\n"
        "Ви також можете натиснути «🔄 Перевірити статус» у будь-який час."
    )
    await message.answer(
        text=user_text,
        reply_markup=get_main_reply_keyboard(access_level=AccessLevel.GUEST),
        parse_mode="HTML",
    )

    # Сповіщення адміністратора системи
    if config.admin_id and config.admin_id != message.from_user.id:
        admin_card = (
            "🔔 <b>Нова заявка на авторизацію монтажника!</b>\n\n"
            f"<b>Користувач:</b> @{message.from_user.username or 'немає'}\n"
            f"<b>Telegram ID:</b> <code>{message.from_user.id}</code>\n"
            f"<b>ПІБ:</b> {surname} {official_name} {patronymic or ''}\n"
            f"<b>Телефон:</b> <code>{phone}</code>\n"
            f"<b>Бажаний позивний:</b> <code>{call_sign}</code>\n\n"
            "Оберіть дію:"
        )
        try:
            await message.bot.send_message(
                chat_id=config.admin_id,
                text=admin_card,
                reply_markup=get_user_approval_keyboard(message.from_user.id),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Не вдалося надіслати картку заявки адміну {config.admin_id}: {e}")


# ---------------------------------------------------------------------------
# Перевірка статусу заявки
# ---------------------------------------------------------------------------
@router.message(F.text == "🔄 Перевірити статус")
async def check_status(
    message: Message,
    user: Optional[UserModel],
    auth_repo: Optional[AuthRepository],
) -> None:
    """Оновлення та перевірка поточного рівня доступу."""
    fresh_user = user
    if auth_repo:
        try:
            fresh_user = await auth_repo.get_user_by_id(message.from_user.id)
        except Exception as e:
            logger.error(f"Помилка отримання статусу користувача: {e}")

    current_level = fresh_user.access_level if fresh_user else AccessLevel.GUEST

    if current_level >= AccessLevel.USER:
        await message.answer(
            f"🎉 <b>Ваш статус оновлено!</b>\n\n"
            f"Поточний рівень: <b>{current_level.badge}</b>\n"
            f"Позивний: <b>{fresh_user.call_sign or 'не призначено'}</b>\n\n"
            "Робоче меню активовано нижче:",
            reply_markup=get_main_reply_keyboard(access_level=current_level),
            parse_mode="HTML",
        )
    elif fresh_user and (fresh_user.phone or fresh_user.call_sign):
        await message.answer(
            "⏳ <b>Ваша заявка знаходиться на розгляді.</b>\n\n"
            f"Позивний: <code>{fresh_user.call_sign or 'не вказано'}</code>\n"
            f"Телефон: <code>{fresh_user.phone or 'не вказано'}</code>\n\n"
            "Адміністратор ще не підтвердив доступ. Будь ласка, очікуйте.",
            reply_markup=get_main_reply_keyboard(access_level=AccessLevel.GUEST),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "ℹ️ <b>Ви ще не заповнили заявку на реєстрацію.</b>\n\n"
            "Натисніть <b>«📝 Подати заявку на реєстрацію»</b> нижче, щоб отримати доступ монтажника.",
            reply_markup=get_main_reply_keyboard(access_level=AccessLevel.GUEST),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------------
# Довідка та контакти для Гостя
# ---------------------------------------------------------------------------
@router.message(F.text == "ℹ️ Довідка та контакти")
async def guest_help_contacts(message: Message) -> None:
    """Інформація для незареєстрованих користувачів."""
    text = (
        "<b>📖 Інформація для гостей Refridex OS</b>\n\n"
        "Цей бот призначений для оперативного обліку монтажів кондиціонерів, "
        "розрахунку фреону та формування звітів по торговельних точках.\n\n"
        "<b>Як отримати доступ монтажника:</b>\n"
        "1. Натисніть «📝 Подати заявку на реєстрацію».\n"
        "2. Надішліть номер телефону, ПІБ та бажаний позивний.\n"
        "3. Після схвалення адміністратором вам відкриється повний робочий функціонал.\n\n"
        "📞 З екстрених питань звертайтеся до чергового диспетчера."
    )
    await message.answer(text=text, parse_mode="HTML")


# ---------------------------------------------------------------------------
# Callback-обробники схвалення/відхилення адміністратором
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("user_approve:"))
async def on_user_approve(callback: CallbackQuery, auth_repo: Optional[AuthRepository]) -> None:
    """Схвалення заявки користувача адміністратором."""
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Некоректний формат команди", show_alert=True)
        return

    target_user_id = int(parts[1])
    target_level = int(parts[2])
    level_enum = AccessLevel(target_level)

    if auth_repo:
        try:
            await auth_repo.update_access_level(
                user_id=target_user_id,
                new_level=target_level,
                changed_by_user_id=callback.from_user.id,
                reason="Схвалено адміністратором через кнопку в боті",
            )
        except Exception as e:
            logger.error(f"Помилка схвалення користувача {target_user_id}: {e}")
            await callback.answer("Помилка оновлення в базі даних", show_alert=True)
            return

    # Оновлюємо картку у чаті адміна
    await callback.message.edit_text(
        f"{callback.message.text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>СХВАЛЕНО!</b> Надано статус: <b>{level_enum.badge}</b>\n"
        f"Адміністратор: @{callback.from_user.username or callback.from_user.id}",
        parse_mode="HTML",
    )
    await callback.answer(f"Користувачу призначено {level_enum.title}")

    # Надсилаємо сповіщення та оновлене меню користувачу
    try:
        await callback.bot.send_message(
            chat_id=target_user_id,
            text=(
                f"🎉 <b>Вітаємо! Вашу заявку схвалено!</b>\n\n"
                f"Вам надано доступ: <b>{level_enum.badge}</b>.\n"
                f"Робоче меню активовано. Ви можете приступати до роботи:"
            ),
            reply_markup=get_main_reply_keyboard(access_level=target_level),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Не вдалося доставити повідомлення користувачу {target_user_id}: {e}")


@router.callback_query(F.data.startswith("user_reject:"))
async def on_user_reject(callback: CallbackQuery) -> None:
    """Відхилення заявки користувача адміністратором."""
    parts = callback.data.split(":")
    if len(parts) != 2:
        await callback.answer("Некоректний формат", show_alert=True)
        return

    target_user_id = int(parts[1])

    await callback.message.edit_text(
        f"{callback.message.text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"❌ <b>ВІДХИЛЕНО</b> адміністратором @{callback.from_user.username or callback.from_user.id}",
        parse_mode="HTML",
    )
    await callback.answer("Заявку відхилено")

    # Сповіщаємо користувача
    try:
        await callback.bot.send_message(
            chat_id=target_user_id,
            text=(
                "⚠️ <b>Вашу заявку на реєстрацію було відхилено.</b>\n\n"
                "Зверніться до бригадира або диспетчера для уточнення причини."
            ),
            reply_markup=get_main_reply_keyboard(access_level=AccessLevel.GUEST),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Не вдалося сповістити користувача {target_user_id}: {e}")

