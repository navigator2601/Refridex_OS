# handlers/guest.py
import re
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import config
from database.models.user import UserModel, AccessLevel
from database.repositories.auth_repo import AuthRepository
from keyboards.reply_keyboard import (
    get_main_reply_keyboard,
    get_contact_request_keyboard,
    get_cancel_keyboard,
)
from keyboards.inline_keyboard import get_user_approval_keyboard
from utils.messages import GuestMessages

logger = logging.getLogger(__name__)

router = Router(name="guest_router")


class GuestRegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()


# ---------------------------------------------------------------------------
# Скасування процесу реєстрації
# ---------------------------------------------------------------------------
@router.message(F.text == "❌ Скасувати")
async def cancel_registration(message: Message, state: FSMContext, user: Optional[UserModel]) -> None:
    """Скидання поточного стану FSM та повернення до головного меню."""
    await state.clear()
    access_level = user.access_level if user else AccessLevel.GUEST
    await message.answer(
        text=GuestMessages.CANCELLED,
        reply_markup=get_main_reply_keyboard(access_level=access_level),
    )


# ---------------------------------------------------------------------------
# Початок подання заявки
# ---------------------------------------------------------------------------
@router.message(F.text == "📝 Подати заявку на реєстрацію")
async def start_registration(message: Message, state: FSMContext, user: Optional[UserModel]) -> None:
    """Початок анкети реєстрації (Крок 1: Номер телефону)."""
    if user and user.access_level >= AccessLevel.USER:
        await message.answer(
            text=GuestMessages.already_authorized(user.access_level.badge),
            reply_markup=get_main_reply_keyboard(access_level=user.access_level),
            parse_mode="HTML",
        )
        return

    await state.set_state(GuestRegistrationStates.waiting_for_phone)
    await message.answer(
        text=GuestMessages.REG_STEP_PHONE,
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
            text=GuestMessages.REG_INVALID_PHONE,
            reply_markup=get_contact_request_keyboard(),
            parse_mode="HTML",
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(GuestRegistrationStates.waiting_for_name)

    await message.answer(
        text=GuestMessages.reg_step_name(phone),
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Крок 2: Обробка імені та завершення реєстрації
# ---------------------------------------------------------------------------
@router.message(GuestRegistrationStates.waiting_for_name, F.text)
async def process_name(
    message: Message,
    state: FSMContext,
    auth_repo: Optional[AuthRepository],
) -> None:
    name = message.text.strip()

    if len(name) < 2:
        await message.answer(
            text=GuestMessages.REG_INVALID_NAME,
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    phone = data.get("phone", "")

    # Зберігаємо ім'я та телефон у базі даних (позивний залишається для адміна)
    if auth_repo:
        try:
            await auth_repo.update_profile(
                user_id=message.from_user.id,
                phone=phone,
                official_name=name,
            )
        except Exception as e:
            logger.error(f"Помилка оновлення профілю користувача {message.from_user.id}: {e}")

    await state.clear()

    # Повідомлення користувачу про успішне надсилання заявки
    await message.answer(
        text=GuestMessages.reg_success_user(phone=phone, name=name),
        reply_markup=get_main_reply_keyboard(access_level=AccessLevel.GUEST),
        parse_mode="HTML",
    )

    # Сповіщення адміністратора системи
    if config.admin_id and config.admin_id != message.from_user.id:
        admin_card = GuestMessages.reg_admin_notification(
            username=message.from_user.username,
            user_id=message.from_user.id,
            name=name,
            phone=phone,
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
            text=GuestMessages.status_approved(current_level.badge, fresh_user.display_name if fresh_user else None),
            reply_markup=get_main_reply_keyboard(access_level=current_level),
            parse_mode="HTML",
        )
    elif fresh_user and (fresh_user.phone or fresh_user.official_name):
        await message.answer(
            text=GuestMessages.status_pending(fresh_user.official_name or fresh_user.first_name, fresh_user.phone),
            reply_markup=get_main_reply_keyboard(access_level=AccessLevel.GUEST),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            text=GuestMessages.STATUS_NOT_SUBMITTED,
            reply_markup=get_main_reply_keyboard(access_level=AccessLevel.GUEST),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------------
# Довідка та контакти для Гостя
# ---------------------------------------------------------------------------
@router.message(F.text == "ℹ️ Довідка та контакти")
async def guest_help_contacts(message: Message) -> None:
    """Інформація для незареєстрованих користувачів."""
    await message.answer(text=GuestMessages.GUEST_HELP_CONTACTS, parse_mode="HTML")


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
    admin_repr = callback.from_user.username or str(callback.from_user.id)
    await callback.message.edit_text(
        text=GuestMessages.admin_approved_card(callback.message.text or "", level_enum.badge, admin_repr),
        parse_mode="HTML",
    )
    await callback.answer(f"Користувачу призначено {level_enum.title}")

    # Надсилаємо сповіщення та оновлене меню користувачу
    try:
        await callback.bot.send_message(
            chat_id=target_user_id,
            text=GuestMessages.user_approved_notify(level_enum.badge),
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
    admin_repr = callback.from_user.username or str(callback.from_user.id)

    await callback.message.edit_text(
        text=GuestMessages.admin_rejected_card(callback.message.text or "", admin_repr),
        parse_mode="HTML",
    )
    await callback.answer("Заявку відхилено")

    # Сповіщаємо користувача
    try:
        await callback.bot.send_message(
            chat_id=target_user_id,
            text=GuestMessages.USER_REJECTED_NOTIFY,
            reply_markup=get_main_reply_keyboard(access_level=AccessLevel.GUEST),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Не вдалося сповістити користувача {target_user_id}: {e}")
