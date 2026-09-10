# keyboards/reply_keyboard.py
from dataclasses import dataclass
from typing import List
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database.models.user import AccessLevel

BUTTONS_PER_PAGE = 6


@dataclass(frozen=True)
class MenuItem:
    text: str
    min_level: int


# Головний реєстр пунктів меню системи Refridex OS
MENU_ITEMS: List[MenuItem] = [
    # Рівень 0: Гість
    MenuItem(text="📋 Заповнити профіль монтажника", min_level=AccessLevel.GUEST),
    MenuItem(text="ℹ️ Інструкції та допомога", min_level=AccessLevel.GUEST),

    # Рівень 1: Монтажник
    MenuItem(text="❄️ Введення замірів", min_level=AccessLevel.USER),
    MenuItem(text="📍 Мої об'єкти (ТТ)", min_level=AccessLevel.USER),
    MenuItem(text="👤 Мій профіль", min_level=AccessLevel.USER),

    # Рівень 2: Бригадир / Диспетчер
    MenuItem(text="🔍 Пошук по всіх ТТ", min_level=AccessLevel.MODERATOR),
    MenuItem(text="📊 Звірка та вивантаження", min_level=AccessLevel.MODERATOR),

    # Рівень 3: Адміністратор
    MenuItem(text="⚙️ Адмін-панель", min_level=AccessLevel.ADMIN),
    MenuItem(text="👥 Керування користувачами", min_level=AccessLevel.ADMIN),
    MenuItem(text="🤖 Telethon сесії", min_level=AccessLevel.ADMIN),
]


def get_main_reply_keyboard(
    access_level: int = AccessLevel.GUEST,
    page: int = 1,
    buttons_per_page: int = BUTTONS_PER_PAGE,
) -> ReplyKeyboardMarkup:
    """
    Фабрика динамічної Reply-клавіатури головного меню.
    
    1. Фільтрує кнопки за правилом: `item.min_level <= access_level`.
    2. Якщо кількість кнопок перевищує `buttons_per_page`, застосовує пагінацію.
    """
    # 1. Відбираємо дозволені кнопки для поточного рівня доступу
    allowed_items = [item for item in MENU_ITEMS if item.min_level <= access_level]

    total_buttons = len(allowed_items)
    total_pages = max(1, (total_buttons + buttons_per_page - 1) // buttons_per_page)

    # Нормалізація номера сторінки
    current_page = max(1, min(page, total_pages))

    # Зріз кнопок для поточної сторінки
    start_idx = (current_page - 1) * buttons_per_page
    end_idx = start_idx + buttons_per_page
    page_items = allowed_items[start_idx:end_idx]

    builder = ReplyKeyboardBuilder()

    # Додаємо кнопки по 2 у ряд
    for i in range(0, len(page_items), 2):
        row = [KeyboardButton(text=item.text) for item in page_items[i : i + 2]]
        builder.row(*row)

    # Якщо сторінок більше ніж одна, додаємо блок пагінації
    if total_pages > 1:
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(KeyboardButton(text=f"⬅️ Меню стор. {current_page - 1}"))

        nav_buttons.append(KeyboardButton(text=f"📄 {current_page}/{total_pages}"))

        if current_page < total_pages:
            nav_buttons.append(KeyboardButton(text=f"Меню стор. {current_page + 1} ➡️"))

        builder.row(*nav_buttons)

    return builder.as_markup(resize_keyboard=True)

