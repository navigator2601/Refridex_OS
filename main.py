# main.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from utils.logger import setup_logging
from handlers import start_router

logger = logging.getLogger(__name__)


async def main() -> None:
    """Головна точка входу: ініціалізація та запуск бота."""
    # 1. Налаштування логування
    setup_logging()
    logger.info("Запуск системи Refridex OS...")

    # 2. Перевірка конфігурації
    if not config.bot_token:
        logger.critical("BOT_TOKEN не вказано у файлі .env!")
        sys.exit(1)

    # 3. Ініціалізація бота та диспетчера
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # 4. Реєстрація роутерів
    dp.include_router(start_router)

    # 5. Скидання старих оновлень і запуск polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 Бот запущений і очікує повідомлень...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Сесію бота закрито. Роботу завершено.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Роботу бота зупинено користувачем.")
