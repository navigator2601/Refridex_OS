# handlers/start_handler.py
# Обробник команди /start.
# Перевіряє користувача в БД, оновлює/додає нового.
# Відправляє привітальне повідомлення з КНОПКОЮ WEB APP (ПОВНИЙ ЕКРАН).

from aiogram import Router, types, Bot
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
# --- ЗМІНА ІМПОРТІВ: ВИКОРИСТОВУЄМО INLINE КЛАВІАТУРУ ДЛЯ ПОВНОГО ЕКРАНУ ---
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
# -------------------------------------------------------------------------
import logging
import asyncpg
from typing import Any
from aiogram.fsm.context import FSMContext
from handlers.menu_handler import show_main_menu_handler, MenuStates
from database import users_db

logger = logging.getLogger(__name__)

router = Router()

# --- КОНФІГУРАЦІЯ WEB APP ---
WEB_APP_URL = "https://navigator2601.github.io/Refridex_OS/webapp/" 
# ---------------------------

@router.message(CommandStart())
async def command_start_handler(
    message: types.Message,
    bot: Bot,
    db_pool: asyncpg.Pool,
    telethon_manager: Any,
    state: FSMContext
) -> None:
    """
    Обробник команди /start.
    Відправляє привітальне повідомлення з Inline-кнопкою для Web App,
    що дозволяє відкрити його на весь екран.
    """
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_username = message.from_user.username
    user_last_name = message.from_user.last_name

    logger.info(f"Користувач {user_first_name} (ID: {user_id}) виконав команду /start.")

    if not db_pool:
        logger.error("db_pool не знайдено в аргументах обробника start_handler!")
        await message.answer("Виникла внутрішня помилка. Будь ласка, спробуйте пізніше.")
        return

    try:
        # --- ЛОГІКА БД: Перевірка та оновлення користувача ---
        user = await users_db.get_user(db_pool, user_id)
        if user:
            await users_db.update_user_activity(db_pool, user_id)
            logger.info(f"Оновлено last_activity для існуючого користувача {user_id}.")
        else:
            await users_db.add_user(db_pool, user_id, user_username, user_first_name, user_last_name)
            logger.info(f"Додано нового користувача {user_id} до БД.")
        # ----------------------------------------------------
            
        # --- ЛОГІКА КЛАВІАТУРИ WEB APP (INLINE) ---
        # 1. Створення об'єкта WebAppInfo
        web_app_info = WebAppInfo(url=WEB_APP_URL)
        
        # 2. Створення Inline кнопки
        web_app_button = InlineKeyboardButton(
            text="🚀 Запустити Refridex Web App (Повний екран)",
            web_app=web_app_info
        )
        
        # 3. Створення Inline клавіатури
        # Ця клавіатура буде прикріплена до повідомлення і дозволить Fullscreen mode
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [web_app_button],
            ]
        )
        # -----------------------------------------

        welcome_message = f"""
<b>"Вітаю, майстре охолодження, {user_first_name}.</b>
Рефрідекс активовано.
Підключення до бази Конди-Ленду успішне.
Починаю синхронізацію моделей, трас і фреонів.
Твій шлях крізь жар і мідь — під моїм наглядом.
Нехай монтаж буде рівним, а фреон — у нормі."
\n\n<b>Тисни на кнопку нижче, щоб відкрити робочий інтерфейс!</b>
"""
        # !!! ВІДПРАВКА ПОВІДОМЛЕННЯ З INLINE КЛАВІАТУРОЮ !!!
        await message.answer(
            welcome_message, 
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard # Передаємо Inline клавіатуру
        )
        logger.info(f"Відправлено привітальне повідомлення з Fullscreen Web App кнопкою користувачу {user_id}.")

        # Встановлюємо початковий стан FSM та номер сторінки
        await state.set_state(MenuStates.main_menu)
        await state.update_data(menu_page=0)

        # Тепер ми можемо викликати show_main_menu_handler, оскільки він, ймовірно, 
        # також використовує InlineKeyboardMarkup, і конфлікту не буде.
        # Головне меню з'явиться або як редагування цього повідомлення, або як нове повідомлення.
        await show_main_menu_handler(message, bot, db_pool, state)
        logger.info(f"Відображено головне меню для користувача {user_id}.")

    except Exception as e:
        logger.error(f"Помилка обробки команди /start для користувача {user_id}: {e}", exc_info=True)
        await message.answer("Виникла внутрішня помилка. Будь ласка, спробуйте ще раз пізніше.")