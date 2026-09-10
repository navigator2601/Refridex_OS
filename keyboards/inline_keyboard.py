# keyboards/inline_keyboard.py
from typing import Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_block_navigation_keyboard(
    blocks_count: int,
    active_block: int = 1,
    task_id: int = 0,
) -> InlineKeyboardMarkup:
    """
    Контекстна інлайн-клавіатура для перемикання між кондиціонерами об'єкта (К1, К2...).
    Активний блок виділяється маркером 🔹.
    """
    builder = InlineKeyboardBuilder()

    buttons = []
    for i in range(1, blocks_count + 1):
        label = f"🔹 К{i}" if i == active_block else f"К{i}"
        buttons.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"block_select:{task_id}:{i}",
            )
        )

    # Розбиваємо кнопки блоків по 4 в рядок
    for i in range(0, len(buttons), 4):
        builder.row(*buttons[i : i + 4])

    return builder.as_markup()


def get_block_action_keyboard(
    block_num: int,
    task_id: int,
    geo_coords: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    Швидкі контекстні дії для вибраного кондиціонера/об'єкта:
    - «➕ Додати пайку»
    - «📍 Маршрут Google Maps»
    - «✅ Сформувати підсумок»
    """
    builder = InlineKeyboardBuilder()

    # Дія з пайкою
    builder.row(
        InlineKeyboardButton(
            text="➕ Додати пайку",
            callback_data=f"solder_add:{task_id}:{block_num}",
        )
    )

    # Якщо є координати ТТ — генеруємо пряме посилання на навігацію Google Maps
    if geo_coords and geo_coords.strip():
        builder.row(
            InlineKeyboardButton(
                text="📍 Маршрут Google Maps",
                url=f"https://www.google.com/maps/dir/?api=1&destination={geo_coords.strip()}",
            )
        )

    # Підсумок монтажу
    builder.row(
        InlineKeyboardButton(
            text="✅ Сформувати підсумок",
            callback_data=f"summary_make:{task_id}",
        )
    )

    return builder.as_markup()


def get_profile_inline_keyboard() -> InlineKeyboardMarkup:
    """Інлайн-кнопки профілю користувача."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Оновити дані", callback_data="profile_refresh"),
        InlineKeyboardButton(text="✏️ Змінити позивний/ПІБ", callback_data="profile_edit"),
    )
    return builder.as_markup()

