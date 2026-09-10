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
from utils.messages import CommonMessages

logger = logging.getLogger(__name__)

router = Router(name="common_router")


@router.message(CommandStart())
async def cmd_start(message: Message, user: Optional[UserModel]) -> None:
    """Обробка команди /start та первинне вітання."""
    access_level = user.access_level if user else AccessLevel.GUEST
    user_name = user.display_name if user else (message.from_user.full_name if message.from_user else "Користувач")
    badge = access_level.badge

    welcome_text = CommonMessages.welcome(user_name=user_name, badge=badge)

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
    text = CommonMessages.help_text(level=level)
    await message.answer(text=text, parse_mode="HTML")


@router.message(F.text == "👤 Мій профіль")
async def handle_my_profile(message: Message, user: Optional[UserModel]) -> None:
    """Відображення картки власного профілю користувача."""
    if not user:
        await message.answer(text=CommonMessages.PROFILE_NOT_FOUND)
        return

    card = CommonMessages.user_card(user)
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
        text=CommonMessages.pagination_page(page),
        reply_markup=get_main_reply_keyboard(access_level=access_level, page=page),
    )


@router.callback_query(F.data == "profile_refresh")
async def on_profile_refresh(
    callback: CallbackQuery,
    user: Optional[UserModel],
    auth_repo: Optional[AuthRepository],
) -> None:
    """Оновлення інформації профілю."""
    if not user or not auth_repo:
        await callback.answer(CommonMessages.DATA_UNAVAILABLE)
        return

    fresh_user = await auth_repo.get_user_by_id(user.id)
    if not fresh_user:
        await callback.answer(CommonMessages.USER_NOT_FOUND, show_alert=True)
        return

    card = CommonMessages.user_card(fresh_user)
    if callback.message:
        await callback.message.edit_text(
            text=card,
            reply_markup=get_profile_inline_keyboard(),
            parse_mode="HTML",
        )
    await callback.answer(CommonMessages.DATA_REFRESHED)


@router.callback_query(F.data == "profile_edit")
async def on_profile_edit(callback: CallbackQuery) -> None:
    """Підказка щодо зміни даних."""
    await callback.answer(
        CommonMessages.PROFILE_EDIT_ALERT,
        show_alert=True,
    )
