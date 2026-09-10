# handlers/navigator.py
import logging
from aiogram import Router, F
from aiogram.types import Message

from database.models.user import UserModel, AccessLevel
from filters.role_filter import RoleFilter

logger = logging.getLogger(__name__)

router = Router(name="navigator_router")
# Доступ для користувачів від рівня TECHNO_NAVIGATOR (L1+) і вище
router.message.filter(RoleFilter(min_level=AccessLevel.TECHNO_NAVIGATOR))


@router.message(F.text == "📚 Каталог")
async def handle_catalog(message: Message, user: UserModel) -> None:
    """Перегляд каталогу обладнання."""
    await message.answer(
        "📚 <b>Каталог кліматичного обладнання</b>\n\n"
        "Оберіть категорію:\n"
        "• Спліт-системи (7, 9, 12, 18, 24)\n"
        "• Касетні кондиціонери\n"
        "• Канальні та підстельові блоки\n"
        "• Мульти-спліт системи",
        parse_mode="HTML",
    )


@router.message(F.text == "📖 Довідники")
async def handle_reference(message: Message, user: UserModel) -> None:
    """Довідники та технічні норми."""
    await message.answer(
        "📖 <b>Технічні довідники Refridex</b>\n\n"
        "• Таблиці відповідності фреонів (R410A, R32, R407C)\n"
        "• Граничні довжини трас та перепади висот\n"
        "• Норми вакуумування та перевірки тиску",
        parse_mode="HTML",
    )


@router.message(F.text == "🕵️ Пошук")
async def handle_search(message: Message, user: UserModel) -> None:
    """Швидкий глобальний пошук."""
    await message.answer(
        "🕵️ <b>Швидкий пошук</b>\n\n"
        "Введіть запит для пошуку (модель кондиціонера, код помилки або номер ТТ):",
        parse_mode="HTML",
    )


@router.message(F.text == "⚠️ Коди помилок")
async def handle_error_codes(message: Message, user: UserModel) -> None:
    """База кодів несправностей та діагностики."""
    await message.answer(
        "⚠️ <b>База кодів помилок кондиціонерів</b>\n\n"
        "Введіть код помилки або оберіть виробника (Gree, Cooper&Hunter, Daikin, Midea, Mitsubishi):",
        parse_mode="HTML",
    )


@router.message(F.text == "🛠️ Інструкції")
async def handle_instructions(message: Message, user: UserModel) -> None:
    """Сервісні мануали та інструкції монтажу."""
    await message.answer(
        "🛠️ <b>Сервісні інструкції та стандарти монтажу</b>\n\n"
        "1. Регламент прокладання фреонової магістралі\n"
        "2. Правила вальцювання та пайки мідних з'єднань\n"
        "3. Пусконалагодження та вимірювання струмів компресора",
        parse_mode="HTML",
    )

