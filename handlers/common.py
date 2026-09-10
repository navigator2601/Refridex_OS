# handlers/common.py
import re
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from database.models.user import UserModel, AccessLevel
from database.repositories.auth_repo import AuthRepository
from keyboards.reply_keyboard import get_main_reply_keyboard
from keyboards.inline_keyboard import get_profile_inline_keyboard

logger = logging.getLogger(__name__)

router = Router(name="common_router")


def format_user_card(user: UserModel) -> str:
    """Форматування інформаційної картки користувача."""
    role_badge = user.access_level.badge
    status = "✅ Авторизовано" if user.is_authorized else "⏳ Очікує підтвердження"
    
    text = (
        f"<b>{role_badge}</b>\n\n"
        f"<b>ID:</b> <code>{user.id}</code>\n"
        f"<b>Користувач:</b> @{user.username if user.username else 'не вказано'}\n"
        f"<b>ПІБ:</b> {user.surname or ''} {user.official_name or user.first_name or ''} {user.patronymic or ''}\n"
        f"<b>Позивний:</b> {user.call_sign or 'не призначено'}\n"
        f"<b>Телефон:</b> {user.phone or 'не вказано'}\n"
        f"<b>Статус:</b> {status}\n"
    )
    if user.access_level.is_admin():
        text += (
            f"\n<b>Права адміністратора:</b>\n"
            f"• Сесії: {'✅' if user.can_manage_sessions else '❌'}\n"
            f"• Чати: {'✅' if user.can_manage_chats else '❌'}\n"
            f"• Користувачі: {'✅' if user.can_manage_users else '❌'}\n"
        )
    return text.strip()


@router.message(CommandStart())
async def cmd_start(message: Message, user: Optional[UserModel]) -> None:
    """Обробка команди /start та первинне вітання."""
    access_level = user.access_level if user else AccessLevel.GUEST
    user_name = user.display_name if user else message.from_user.full_name
    badge = access_level.badge

    welcome_text = (
        f"👋 Вітаємо в системі <b>Refridex OS</b>, {user_name}!\n\n"
        f"Ваш поточний статус: <b>{badge}</b>\n\n"
        f"Оберіть потрібний розділ у меню нижче:"
    )

    await message.answer(
        text=welcome_text,
        reply_markup=get_main_reply_keyboard(access_level=access_level, page=1),
        parse_mode="HTML",
    )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Інструкції та допомога")
async def cmd_help(message: Message, user: Optional[UserModel]) -> None:
    """Довідка та інструкції відповідно до рівня доступу."""
    level = user.access_level if user else AccessLevel.GUEST

    text = (
        "<b>📖 Довідник Refridex OS</b>\n\n"
        "<b>Основні можливості:</b>\n"
        "• <b>Гість:</b> перегляд інструкцій та реєстрація анкети монтажника.\n"
    )
    if level >= AccessLevel.USER:
        text += (
            "• <b>Монтажник:</b> внесення замірів довжини трас (наприклад: <code>130+340+530</code>), "
            "додавання пайок, перегляд закріплених ТТ та маршрутизація через Google Maps.\n"
        )
    if level >= AccessLevel.MODERATOR:
        text += (
            "• <b>Бригадир / Диспетчер:</b> пошук замовлень по всіх торгових точках, "
            "звірка виконаних робіт, вивантаження звітів.\n"
        )
    if level >= AccessLevel.ADMIN:
        text += (
            "• <b>Адміністратор:</b> керування Telethon-сесіями, білим списком чатів "
            "та наданням прав користувачам.\n"
        )

    text += "\nДля повернення використовуйте кнопки головного меню."
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "👤 Мій профіль")
async def handle_my_profile(message: Message, user: Optional[UserModel]) -> None:
    """Відображення картки власного профілю користувача."""
    if not user:
        await message.answer("⚠️ Не вдалося завантажити профіль. Спробуйте /start")
        return

    card = format_user_card(user)
    await message.answer(
        text=card,
        reply_markup=get_profile_inline_keyboard(),
        parse_mode="HTML",
    )




@router.message(F.text.regexp(r"^⬅️ Меню стор\. (\d+)$"))
@router.message(F.text.regexp(r"^Меню стор\. (\d+) ➡️$"))
async def handle_menu_pagination(message: Message, user: Optional[UserModel]) -> None:
    """Перемикання сторінок головного Reply-меню."""
    access_level = user.access_level if user else AccessLevel.GUEST
    match = re.search(r"(\d+)", message.text or "")
    page = int(match.group(1)) if match else 1

    await message.answer(
        f"📄 Меню (сторінка {page}):",
        reply_markup=get_main_reply_keyboard(access_level=access_level, page=page),
    )


@router.callback_query(F.data == "profile_refresh")
async def on_profile_refresh(callback: CallbackQuery, user: Optional[UserModel], auth_repo: Optional[AuthRepository]) -> None:
    """Оновлення інформації профілю."""
    if not user or not auth_repo:
        await callback.answer("⚠️ Дані недоступні")
        return

    fresh_user = await auth_repo.get_user_by_id(user.id)
    if not fresh_user:
        await callback.answer("Користувача не знайдено", show_alert=True)
        return

    card = format_user_card(fresh_user)
    await callback.message.edit_text(
        text=card,
        reply_markup=get_profile_inline_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("✅ Дані оновлено")


@router.callback_query(F.data == "profile_edit")
async def on_profile_edit(callback: CallbackQuery) -> None:
    """Підказка щодо зміни даних."""
    await callback.answer(
        "Зміна позивного та персональних даних здійснюється через адміністратора.",
        show_alert=True,
    )

