# handlers/start_handler.py
"""
Обробник команди /start.
Перевіряє користувача в БД telethon_auth, добавляє якщо його немає.
Показує головне меню при нормальному доступі.
"""

from aiogram import Router, types, Bot
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import logging
import asyncpg
from typing import Any
from aiogram.fsm.context import FSMContext

# НОВИЙ ІМПОРТ для роботи з новою схемою
from database.telethon_auth_db import (
    get_user_by_id,
    create_user,
    update_user,
    get_user_access_level,
    log_auth_attempt
)
from database.db_pool_manager import get_db_pool

logger = logging.getLogger(__name__)

router = Router()

# --- КОНФІГУРАЦІЯ WEB APP ---
WEB_APP_URL = "https://navigator2601.github.io/Refridex_OS/webapp/"
# ---------------------------


@router.message(CommandStart())
async def command_start_handler(
    message: types.Message,
    bot: Bot,
    state: FSMContext
) -> None:
    """
    Обробник команди /start.
    
    Логіка:
    1. Перевіряє чи існує користувач у telethon_auth.users
    2. Якщо немає - додає його з access_level = 0 (GUEST)
    3. Якщо існує - оновлює last_activity
    4. Перевіряє рівень доступу
    5. Показує привітання та меню
    """
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name or "Друже"
    user_username = message.from_user.username
    user_last_name = message.from_user.last_name

    logger.info(f"👤 Користувач {user_first_name} (ID: {user_id}) виконав команду /start.")

    # Отримуємо пул подключений
    try:
        db_pool = await get_db_pool()
    except Exception as e:
        logger.error(f"❌ Помилка при отриманні пула БД: {e}", exc_info=True)
        await message.answer("❌ Виникла помилка з'єднання з базою даних. Спробуйте пізніше.")
        return

    try:
        # ===== КРОК 1: Перевіряємо наявність користувача =====
        user = await get_user_by_id(db_pool, user_id)

        if user:
            # Користувач існує - оновлюємо last_activity
            logger.info(f"✅ Користувач {user_id} знайдений у БД.")
            await update_user(
                db_pool,
                user_id,
                last_activity=None  # Функція встановить CURRENT_TIMESTAMP
            )
            logger.info(f"✅ Оновлено last_activity для користувача {user_id}.")
        else:
            # Користувач не існує - додаємо його
            logger.info(f"➕ Користувач {user_id} не знайдений. Додаємо до БД...")
            success = await create_user(
                db_pool,
                user_id=user_id,
                username=user_username,
                first_name=user_first_name,
                last_name=user_last_name,
                access_level=0,  # GUEST - за умовчанням
                is_authorized=False
            )
            
            if not success:
                logger.warning(f"⚠️ Не вдалося додати корис��увача {user_id}.")
                await message.answer("⚠️ Виникла помилка при реєстрації. Спробуйте пізніше.")
                return
            
            logger.info(f"✅ Користувач {user_id} успішно додан до БД з access_level = 0.")

        # ===== КРОК 2: Отримуємо рівень доступу =====
        access_level = await get_user_access_level(db_pool, user_id)
        logger.info(f"🔐 Рівень доступу користувача {user_id}: {access_level}")

        # ===== КРОК 3: Логуємо успішну авторизацію =====
        await log_auth_attempt(
            db_pool,
            user_id=user_id,
            phone_number=None,
            session_id=None,
            auth_status="SUCCESS",
            error_message=None
        )

        # ===== КРОК 4: Готуємо привітання =====
        greeting_message = (
            f"👋 Привіт, {user_first_name}!\n\n"
            f"Ласкаво просимо до <b>Refridex OS</b> 🎛️\n\n"
            f"Рівень доступу: <b>{get_access_level_name(access_level)}</b>"
        )

        # ===== КРОК 5: Готуємо клавіатуру з Web App =====
        keyboard = create_start_keyboard(access_level)

        # ===== КРОК 6: Відправляємо повідомлення =====
        await message.answer(
            greeting_message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

        logger.info(f"✅ Обробник /start завершено успішно для користувача {user_id}.")

    except Exception as e:
        logger.error(f"❌ Помилка в обробнику /start для користувача {user_id}: {e}", exc_info=True)
        await message.answer("❌ Виникла помилка. Спробуйте пізніше.")


def get_access_level_name(access_level: int) -> str:
    """
    Перетворює числовий рівень доступу на читаний вигляд.
    
    Args:
        access_level: 0=GUEST, 1=USER, 2=MODERATOR, 3=ADMIN
        
    Returns:
        Назва рівня доступу
    """
    levels = {
        0: "👤 GUEST (Гість)",
        1: "👨 USER (Користувач)",
        2: "👮 MODERATOR (Модератор)",
        3: "👑 ADMIN (Адміністратор)"
    }
    return levels.get(access_level, "❓ НЕВІДОМО")


def create_start_keyboard(access_level: int) -> InlineKeyboardMarkup:
    """
    Створює клавіатуру для стартового повідомлення.
    Кнопки залежать від рівня доступу.
    
    Args:
        access_level: рівень доступу користувача
        
    Returns:
        InlineKeyboardMarkup з кнопками
    """
    builder = InlineKeyboardMarkup(inline_keyboard=[
        # Основна кнопка для всіх
        [
            InlineKeyboardButton(
                text="🌐 Відкрити WebApp",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        # Кнопка адмін-панелі для адміністраторів (access_level >= 3)
        [
            InlineKeyboardButton(
                text="⚙️ Адмін-панель",
                callback_data="admin_menu"
            )
        ] if access_level >= 3 else [],
        # Кнопка управління дозволами для модераторів і вище
        [
            InlineKeyboardButton(
                text="🔐 Управління користувачами",
                callback_data="manage_users"
            )
        ] if access_level >= 2 else [],
        # Кнопка довідки
        [
            InlineKeyboardButton(
                text="❓ Довідка",
                callback_data="help"
            )
        ]
    ])
    
    # Видаляємо пусті рядки
    builder.inline_keyboard = [row for row in builder.inline_keyboard if row]
    
    return builder