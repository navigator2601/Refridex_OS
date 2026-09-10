# handlers/start.py
import logging
from aiogram import Router, types
from aiogram.filters import CommandStart

from services.messages import messages

logger = logging.getLogger(__name__)
router = Router(name="start_router")


@router.message(CommandStart())
async def handle_start(message: types.Message) -> None:
    """Обробник команди /start."""
    user = message.from_user
    user_name = user.first_name if user else None
    logger.info(f"Користувач {user.id if user else 'невідомий'} ({user_name}) викликав /start")

    # Отримуємо текст повідомлення з сервісу шаблонів / генерації
    welcome_text = messages.get_welcome_message(user_name=user_name)
    await message.answer(welcome_text)

