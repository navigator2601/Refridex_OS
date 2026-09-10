# handlers/montage.py
import logging
from aiogram import Router, F
from aiogram.types import Message

from database.models.user import UserModel, AccessLevel
from filters.role_filter import RoleFilter

logger = logging.getLogger(__name__)

router = Router(name="montage_router")
# Доступ лише для користувачів з рівнем USER і вище
router.message.filter(RoleFilter(min_level=AccessLevel.USER))


@router.message(F.text == "❄️ Введення замірів")
async def handle_montage_measurements(message: Message, user: UserModel) -> None:
    """Старт процесу введення замірів трас кондиціонерів."""
    await message.answer(
        f"❄️ <b>Введення замірів магістралей</b>\n\n"
        f"Монтажник: <b>{user.display_name}</b>\n\n"
        f"Для початку введення оберіть об'єкт зі списку «📍 Мої об'єкти (ТТ)» "
        f"або введіть номер/код торговельної точки (наприклад: <code>А3406</code>).",
        parse_mode="HTML",
    )


@router.message(F.text == "📍 Мої об'єкти (ТТ)")
async def handle_my_stores(message: Message, user: UserModel) -> None:
    """Список торгових точок, закріплених за монтажником."""
    await message.answer(
        "📍 <b>Закріплені об'єкти (ТТ)</b>\n\n"
        "Наразі немає активних призначених завдань.\n"
        "Нові завдання з'являтимуться автоматично після обробки заявок у робочих групах.",
        parse_mode="HTML",
    )

