# handlers/montage.py
import logging
from aiogram import Router, F
from aiogram.types import Message

from database.models.user import UserModel, AccessLevel
from filters.role_filter import RoleFilter

logger = logging.getLogger(__name__)

router = Router(name="montage_router")
# Доступ для Системних Інженерів (L3+) і вище
router.message.filter(RoleFilter(min_level=AccessLevel.SYSTEM_ENGINEER))


@router.message(F.text == "📐 Додаткові функції")
async def handle_extra_features(message: Message, user: UserModel) -> None:
    """Додаткові функції розрахунків монтажу."""
    await message.answer(
        "📐 <b>Додаткові інженерні функції [L3]</b>\n\n"
        "• Калькулятор дозаправки фреону R410A / R32\n"
        "• Таблиця діаметрів мідних труб та ізоляції\n"
        "• Електричні схеми міжблочних підключень",
        parse_mode="HTML",
    )


@router.message(F.text == "🅰️ Пошук магазинів")
async def handle_store_search(message: Message, user: UserModel) -> None:
    """Пошук магазинів або точок монтажу."""
    await message.answer(
        "🅰️ <b>Пошук магазинів та об'єктів</b>\n\n"
        "Введіть номер або код торговельної точки (наприклад: <code>А3406</code> або <code>3406</code>):",
        parse_mode="HTML",
    )


@router.message(F.text == "🔄 Отримати список ТТ")
async def handle_get_tt_list(message: Message, user: UserModel) -> None:
    """Отримання списку активних торговельних точок."""
    await message.answer(
        "🔄 <b>Список активних торговельних точок</b>\n\n"
        "📍 Актуальний реєстр об'єктів синхронізується з чергою замовлень Telethon.\n"
        "Очікуйте оновлення списку завдань.",
        parse_mode="HTML",
    )


@router.message(F.text == "📝 Завдання в роботі")
async def handle_tasks_in_progress(message: Message, user: UserModel) -> None:
    """Перегляд поточних завдань у роботі."""
    await message.answer(
        f"📝 <b>Завдання в роботі</b>\n\n"
        f"Інженер: <b>{user.display_name}</b>\n"
        "На даний момент активних незавершених завдань немає.",
        parse_mode="HTML",
    )


@router.message(F.text == "🧾 Звіт по роботі")
async def handle_work_report(message: Message, user: UserModel) -> None:
    """Формування підсумкового звіту монтажу."""
    await message.answer(
        "🧾 <b>Звіт по виконаній роботі</b>\n\n"
        "Оберіть завершений об'єкт для формування підсумкового табелю та розрахунку матеріалів.",
        parse_mode="HTML",
    )


@router.message(F.text == "🚗 Пробіг")
async def handle_mileage(message: Message, user: UserModel) -> None:
    """Облік пробігу та маршрутів бригади."""
    await message.answer(
        "🚗 <b>Облік службового пробігу</b>\n\n"
        "Введіть показники одометра або кілометраж поїздки (наприклад: <code>45 км</code>):",
        parse_mode="HTML",
    )
