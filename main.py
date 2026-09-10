# main.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart

from config import config

# Налаштування базового логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Ініціалізація бота та диспетчера
bot = Bot(
    token=config.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: types.Message) -> None:
    """Обробник команди /start — привітальне повідомлення."""
    user_name = message.from_user.first_name if message.from_user else "користувачу"
    text = (
        f"👋 <b>Привіт, {user_name}!</b>\n\n"
        "Ласкаво просимо до <b>Refridex OS</b>! ❄️\n"
        "Бот успішно запущений і готовий до роботи."
    )
    await message.answer(text)


async def main() -> None:
    """Головна функція запуску бота."""
    logger.info("Запуск бота Refridex OS...")

    # Скидаємо старі накопичені апдейти
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("🚀 Бот запущений і очікує повідомлень...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Сесію бота закрито.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Роботу бота зупинено.")

