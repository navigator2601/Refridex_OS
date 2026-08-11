# main.py
import asyncio
import logging
from typing import Any

# Імпорти Aiogram
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# Імпорти для вашої конфігурації та логування
from config import config
from utils.logger import setup_logging

# Імпорти для БД та Мідлвари
from database.db_pool_manager import create_db_pool, close_db_pool, init_db_tables, get_db_pool
from middlewares.db_middleware import DbSessionMiddleware
# --- НОВИЙ ІМПОРТ ДЛЯ ОБРОБНИКА ВИКЛЮЧЕНЬ ---
from middlewares.exception_middleware import ExceptionHandlingMiddleware
# --------------------------------------------

# --- НОВІ ІМПОРТИ для Telethon ---
from telegram_client_module.telethon_client import TelethonClientManager
from middlewares.telethon_middleware import TelethonClientMiddleware
# -----------------------------------

# Імпорти для роутерів
from handlers.start_handler import router as start_router
from handlers.menu_handler import router as menu_router

# <--- НОВІ ІМПОРТИ ДЛЯ РОУТЕРІВ АДМІН-ПАНЕЛІ --->
from handlers.admin.main_menu import router as admin_main_menu_router
from handlers.admin.user_management import router as user_management_router
from handlers.admin.telethon_operations import router as telethon_operations_router
from handlers.admin.chat_matrix_handlers import router as chat_matrix_router # <--- ДОДАНО: Імпорт роутера для Чат-матриці
# <------------------------------------------------->
# <--- ДОДАНО НОВИЙ ІМПОРТ ДЛЯ АБО РЕДАГУВАННЯ ДОДАВАННЯ ДАНИХ ДО БД--->
from handlers.admin.db_operations import router as db_operations_router 
# ----------------------------
from handlers.odometer_handler import router as odometer_router
# Підключення ехо для обробки некомандних повідомлень
from handlers.echo_handler import router as echo_router

# НАЙПЕРШИЙ ВИКЛИК налаштування логів
setup_logging()
logger = logging.getLogger(__name__)

# Глобальний екземпляр TelethonManager
telethon_manager: TelethonClientManager = None

async def on_bot_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    """
    Функція, що виконується при запуску бота.
    Ініціалізує пул підключень до БД, таблиці та Telethon-клієнти.
    """
    logger.info("Початок запуску бота. Зареєстровані startup-хуки виконуються.")

    logger.info("Спроба створити пул підключень до бази даних.")
    try:
        await create_db_pool()
        db_pool_instance = await get_db_pool()
        dispatcher.workflow_data['db_pool'] = db_pool_instance
        logger.info("Пул підключень до бази даних створено успішно.")
    except Exception as e:
        logger.critical(f"Критична помилка підключення до бази даних: {e}", exc_info=True)
        await bot.session.close()
        exit(1)

    logger.info("Ініціалізація таблиць бази даних.")
    try:
        await init_db_tables()
        logger.info("Таблиці бази даних ініціалізовано.")
    except Exception as e:
        logger.error(f"Помилка ініціалізації таблиць БД: {e}", exc_info=True)

    # --- ЛОГІКА TELETHON: ІНІЦІАЛІЗАЦІЯ та ЗАПУСК ---
    global telethon_manager

    if telethon_manager and config.telethon_client_enabled:
        logger.info("Ініціалізація TelethonClientManager.")
        await telethon_manager.initialize(db_pool_instance)
        logger.info("TelethonClientManager ініціалізовано.")
        logger.info("Telethon клієнти налаштовано та, якщо потрібно, запущені (через initialize()).")
    else:
        logger.warning("Telethon клієнти вимкнено через конфігурацію або TelethonClientManager не був ініціалізований.")
    # --------------------------------------------------

    logger.info("Завершення on_startup.")

async def on_bot_shutdown(bot: Bot, dispatcher: Dispatcher) -> None:
    """
    Функція, що виконується при завершенні роботи бота.
    Закриває пул підключень до БД та відключає Telethon-клієнти.
    """
    logger.info("Початок завершення роботи бота. Зареєстровані shutdown-хуки виконуються.")

    global telethon_manager
    if telethon_manager and config.telethon_client_enabled:
        logger.info("Спроба відключити Telethon клієнтів.")
        try:
            await telethon_manager.shutdown_all_clients()
            logger.info("Telethon клієнти відключено.")
        except Exception as e:
            logger.error(f"Помилка відключення Telethon клієнтів: {e}", exc_info=True)
    elif config.telethon_client_enabled:
        logger.warning("TelethonClientManager не був ініціалізований або доступний під час завершення роботи.")

    logger.info("Спроба закрити пул підключень до бази даних.")
    try:
        await close_db_pool()
        logger.info("Пул підключень до бази даних закрито.")
    except Exception as e:
        logger.error(f"Помилка закриття пулу БД: {e}", exc_info=True)

    logger.info("Закриття сесію бота.")
    await bot.session.close()
    logger.info("Сесію бота закрито.")

async def main():
    logger.info("Початок виконання головної асинхронної функції 'main'.")

    # ВИПРАВЛЕННЯ: Тепер config.bot_token є звичайним рядком
    bot_token_value = config.bot_token

    if not bot_token_value:
        logger.critical("BOT_TOKEN не встановлено у файлі конфігурації. Будь ласка, перевірте .env та config.py.")
        return

    default_props = DefaultBotProperties(parse_mode=ParseMode.HTML)

    logger.info("Ініціалізація об'єкта Bot.")
    bot = Bot(token=bot_token_value, default=default_props)

    storage = MemoryStorage()

    logger.info("Ініціалізація об'єкта Dispatcher.")
    dp = Dispatcher(storage=storage)

    logger.info("Реєстрація DbSessionMiddleware.")
    dp.update.outer_middleware.register(DbSessionMiddleware())
    logger.info("DbSessionMiddleware зареєстровано глобально.")

    # --- РЕЄСТРАЦІЯ TELETHON МІДЛВАРИ ТА ІНІЦІАЛІЗАЦІЯ TELETHON_MANAGER ---
    global telethon_manager

    if config.telethon_client_enabled:
        logger.info("Ініціалізація глобального TelethonClientManager.")
        telethon_manager = TelethonClientManager(
            api_id=config.api_id,
            api_hash=config.api_hash
        )
        dp.workflow_data['telethon_manager'] = telethon_manager
        logger.info("TelethonClientManager додано до dispatcher.workflow_data.")

        logger.info("Реєстрація TelethonClientMiddleware.")
        dp.update.outer_middleware.register(TelethonClientMiddleware())
        logger.info("TelethonClientMiddleware зареєстровано глобально.")
    else:
        logger.warning("TelethonClientMiddleware не реєструється (вимкнено через конфігурацію).")
    # ------------------------------------

    # --- РЕЄСТРАЦІЯ MIDDLEWARE ДЛЯ ОБРОБКИ ВИКЛЮЧЕНЬ (ОСТАННІЙ OUTER MIDDLEWARE) ---
    logger.info("Реєстрація ExceptionHandlingMiddleware (для централізованої обробки помилок).")
    dp.update.outer_middleware.register(ExceptionHandlingMiddleware())
    logger.info("ExceptionHandlingMiddleware зареєстровано глобально.")
    # -----------------------------------------------------------------------------

    # Реєстрація роутерів
    logger.info("Реєстрація роутера 'start_handler'.")
    dp.include_router(start_router)

    logger.info("Реєстрація роутера 'menu_handler'.")
    dp.include_router(menu_router)

    # ДОДАЄМО РОУТЕР КАТАЛОГУ
    from handlers.catalog_handler import router as catalog_router
    logger.info("Реєстрація роутера 'catalog_handler'.")
    dp.include_router(catalog_router)

    # ДОДАЄМО РОУТЕР ДЛЯ ПРОБІГУ
    logger.info("Реєстрація роутера 'odometer_handler'.")
    dp.include_router(odometer_router)

    logger.info("Реєстрація роутерів адмін-панелі.")
    dp.include_router(admin_main_menu_router)
    dp.include_router(user_management_router)
    dp.include_router(telethon_operations_router)
    dp.include_router(chat_matrix_router) # <--- ДОДАНО: Включення роутера Чат-матриці
    
    # <--- ДОДАНО НОВИЙ РОУТЕР ДЛЯ ДОДАВАННЯ ЧИ РЕДАГУВАННЯ ДАНИХ В БД--->
    logger.info("Реєстрація роутера 'db_operations_handler'.")
    dp.include_router(db_operations_router)
    # ----------------------------

    # echo_router для обробки некомандних повідомлень (завжди останнім!)
    logger.info("Реєстрація роутера 'echo_handler' (для невідомих кнопок та повідомлень).")
    dp.include_router(echo_router)

    # Реєстрація функцій запуску/зупинки
    dp.startup.register(on_bot_startup)
    dp.shutdown.register(on_bot_shutdown)

    logger.info("Перед викликом dp.start_polling. Бот чекає на оновлення...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критична помилка під час polling: {e}", exc_info=True)

    logger.info("dp.start_polling завершив роботу.")

if __name__ == "__main__":
    logger.info("Ядро ініціалізовано: активація блоку `if __name__ == '__main__'` розпочата...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот зупинено вручну (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"Критична помилка в основному циклі: {e}", exc_info=True)
    logger.info("Система: процес завершено. Вихід з потоку.")