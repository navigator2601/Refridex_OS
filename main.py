# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database.db_pool_manager import create_db_pool, close_db_pool
from handlers import main_router
from middlewares.auth_middleware import AuthMiddleware
from middlewares.db_middleware import DbSessionMiddleware
from utils.logger import setup_logger

logger = logging.getLogger("refridex_os")


async def main() -> None:
    """Точка входу та запуск життєвого циклу бота Refridex OS."""
    setup_logger()
    logger.info("Запуск системи Refridex OS...")

    # Ініціалізація пулу підключень PostgreSQL
    pool = await create_db_pool()

    # Ініціалізація екземплярів бота та диспетчера Aiogram v3
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Реєстрація глобальних middleware (порядок важливий: спочатку DB, потім Auth)
    dp.update.outer_middleware(DbSessionMiddleware(pool=pool))
    dp.update.outer_middleware(AuthMiddleware(pool=pool))

    # Підключення роутерів
    dp.include_router(main_router)

    # Реєстрація хуків завершення роботи
    async def on_shutdown() -> None:
        logger.info("Зупинка бота та закриття пулу бази даних...")
        await close_db_pool()
        await bot.session.close()
        logger.info("Бот успішно зупинено.")

    dp.shutdown.register(on_shutdown)

    # Очищення черги накопичених оновлень та старт Long Polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Refridex OS успішно запущено в режимі Polling.")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Отримано сигнал переривання.")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass

