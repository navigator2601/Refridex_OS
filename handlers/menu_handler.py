# Файл: handlers/menu_handler.py
# Призначення: Обробка натискань кнопок головного меню та команд.
# Містить логіку навігації, переходу до адмін-панелі та новий функціонал пошуку.

import logging
import math

from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

import asyncpg

from keyboards.reply_keyboard import get_main_menu_keyboard, get_main_menu_pages_info, get_cancel_keyboard
from keyboards.admin_keyboard import get_admin_main_keyboard
# --- ВИПРАВЛЕНО: Використовуємо єдину функцію з telethon_auth_db ---
from database.telethon_auth_db import get_user_access_level
#from database.db_search_functions import find_in_database, format_search_results
from common.messages import (
    get_access_level_description,
    get_random_admin_welcome_message,
    HELP_MESSAGE_TEXT,
    INFO_MESSAGE_TEXT,
    FIND_MESSAGE_TEXT,
    SEARCH_PROMPT,
    SEARCH_NO_RESULTS
)
from common.constants import BUTTONS_PER_PAGE, ALL_MENU_BUTTONS, ACCESS_LEVEL_BUTTONS

from common.states import AdminStates, MenuStates

logger = logging.getLogger(__name__)

router = Router()

# ЦЕЙ ОБРОБНИК МАЄ БУТИ ПЕРШИМ!
# Він буде спрацьовувати для ручного введення "каталог"
@router.message(F.text.lower() == "каталог")
async def show_catalog_from_text_handler(message: types.Message, db_pool: asyncpg.Pool, state: FSMContext):
    """
    Обробляє запит на показ каталогу, введений вручну.
    """
    await show_catalog_handler(message, db_pool, state)



@router.message(F.text == "⬅️ Назад", MenuStates.main_menu)
@router.message(F.text == "➡️ Іще", MenuStates.main_menu)
@router.message(F.text == "На головну", MenuStates.any)
async def show_main_menu_handler(
    message: types.Message,
    bot: Bot,
    db_pool: asyncpg.Pool,
    state: FSMContext
) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    is_pagination_action_forward = message.text == "➡️ Іще"
    is_pagination_action_backward = message.text == "⬅️ Назад"
    is_main_menu_return = message.text == "На головну"
    is_initial_menu_entry = not (is_pagination_action_forward or is_pagination_action_backward or is_main_menu_return)

    logger.info(f"Користувач {user_name} (ID: {user_id}) викликав show_main_menu_handler (дія: {message.text}).")

    if not db_pool:
        logger.error("db_pool не знайдено в аргументах show_main_menu_handler!")
        await message.answer("Виникла внутрішня помилка. Будь ласка, спробуйте пізніше.")
        return

    access_level = await get_user_access_level(db_pool, user_id)
    if access_level is None:
        access_level = 0
    logger.info(f"Користувач {user_name} (ID: {user_id}) має рівень доступу: {access_level}.")

    current_state_data = await state.get_data()
    current_page = current_state_data.get("menu_page", 0)

    total_buttons, total_pages = get_main_menu_pages_info(access_level)

    if is_pagination_action_backward:
        current_page = max(0, current_page - 1)
    elif is_pagination_action_forward:
        current_page = min(total_pages - 1, current_page + 1)
    elif is_main_menu_return:
        current_page = 0
        await state.set_state(MenuStates.main_menu)

    await state.update_data(menu_page=current_page)
    
    menu_message_text = ""
    if is_main_menu_return or is_initial_menu_entry:
        level_name, level_description = get_access_level_description(access_level)
        menu_message_text = (
            "Ваш рівень доступу:\n"
            f"<b>{level_name}</b>\n"
            f"{level_description}"
        )
    elif is_pagination_action_forward:
        menu_message_text = "Ви перейшли до наступної сторінки меню."
    elif is_pagination_action_backward:
        menu_message_text = "Ви повернулись до попередньої сторінки меню."
    
    keyboard = await get_main_menu_keyboard(access_level, current_page)
    await message.answer(menu_message_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


# НОВИЙ ОБРОБНИК: Обробляє натискання кнопки "Пошук"
@router.message(F.text == "🕵️ Пошук", MenuStates.main_menu)
async def open_search_menu_handler(message: types.Message, state: FSMContext) -> None:
    """Переводить користувача в режим пошуку."""
    logger.info(f"Користувач {message.from_user.id} перейшов у режим пошуку.")
    await state.set_state(MenuStates.find)
    await message.answer(SEARCH_PROMPT, reply_markup=get_cancel_keyboard(), parse_mode=ParseMode.MARKDOWN)

# НОВИЙ ОБРОБНИК: Обробляє текстовий запит у стані пошуку
@router.message(F.text, MenuStates.find)
async def handle_search_query(message: types.Message, db_pool: asyncpg.Pool, state: FSMContext) -> None:
    """Отримує пошуковий запит, шукає в БД і виводить результат."""
    user_query = message.text
    user_id = message.from_user.id
    
    # Якщо користувач вирішив скасувати пошук
    if user_query.lower() == "скасувати":
        await state.set_state(MenuStates.main_menu)
        keyboard = await get_main_menu_keyboard(db_pool, user_id)
        await message.answer("Пошук скасовано. Ви повернулись в головне меню.", reply_markup=keyboard)
        return

    logger.info(f"Користувач {user_id} надіслав пошуковий запит: '{user_query}'.")

    # Тут ми викликаємо вашу функцію для пошуку в базі даних
    search_results = await find_in_database(db_pool, user_query)
    
    if search_results:
        # Ваш приклад з таблицею
        # Виводимо результати як добре відформатовану таблицю або список
        formatted_results = format_search_results(search_results)
        await message.answer(
            f"**Знайдено {len(search_results)} результатів:**\n\n"
            f"{formatted_results}",
            reply_markup=get_cancel_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.answer(SEARCH_NO_RESULTS, reply_markup=get_cancel_keyboard())


@router.message(F.text == "⚙️ Адміністрування", MenuStates.main_menu)
async def handle_admin_button(
    message: types.Message,
    bot: Bot,
    db_pool: asyncpg.Pool,
    state: FSMContext
) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    logger.info(f"Користувач {user_name} (ID: {user_id}) натиснув кнопку '⚙️ Адміністрування'.")

    if not db_pool:
        logger.error("db_pool не знайдено в аргументах handle_admin_button!")
        await message.answer("Виникла внутрішня помилка. Будь ласка, спробуйте пізніше.")
        return

    access_level = await get_user_access_level(db_pool, user_id)
    if access_level is None:
        access_level = 0
    
    if access_level >= 10:
        admin_keyboard = get_admin_main_keyboard()
        
        welcome_admin_text = get_random_admin_welcome_message()
        await state.set_state(AdminStates.admin_main)
        
        await message.answer(
            f"{welcome_admin_text}",
            reply_markup=admin_keyboard,
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Користувачу {user_id} (рівень {access_level}) відображено панель адміністратора.")
    else:
        await message.answer(
            "У вас немає доступу до панелі адміністратора.",
            reply_markup=await get_main_menu_keyboard(access_level, 0)
        )
        logger.warning(f"Користувач {user_id} (рівень {access_level}) спробував отримати доступ до адмін-панелі без дозволу.")

@router.message(Command("help"))
async def command_help_handler(message: types.Message) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logger.info(f"Користувач {user_name} (ID: {user_id}) виконав команду /help.")
    await message.answer(HELP_MESSAGE_TEXT, parse_mode=ParseMode.HTML)

@router.message(Command("info"))
async def command_info_handler(message: types.Message) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logger.info(f"Користувач {user_name} (ID: {user_id}) виконав команду /info.")
    await message.answer(INFO_MESSAGE_TEXT, parse_mode=ParseMode.HTML)

@router.message(Command("find"))
async def command_find_handler(message: types.Message) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logger.info(f"Користувач {user_name} (ID: {user_id}) виконав команду /find.")
    await message.answer(FIND_MESSAGE_TEXT, parse_mode=ParseMode.HTML)