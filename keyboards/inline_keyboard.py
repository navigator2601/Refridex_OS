# відносний шлях до файлу: keyboards/inline_keyboard.py
# Призначення: Функції для створення інлайн-клавіатур.

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict

# Імпортуємо нову функцію
from services.message_formatter import get_model_word_form

async def get_brands_inline_keyboard(brands: List[Dict]) -> InlineKeyboardMarkup:
    """
    Створює інлайн-клавіатуру з кнопками для кожного бренду.
    Кожна кнопка має назву бренду та кількість моделей.
    """
    keyboard_buttons = []
    current_row = []
    
    # Створення кнопок для кожного бренду.
    for brand in brands:
        brand_name = brand['Бренд']
        model_count = brand['Кількість моделей']
        
        # Використовуємо функцію для відмінювання слова 'модель'
        word_form = get_model_word_form(model_count)
        
        # Виправлено: прибрано HTML-теги з тексту кнопки, оскільки Telegram не підтримує їх
        # та використано функцію відмінювання.
        button_text = f"{brand_name} ({model_count} {word_form})"
        callback_data = f"brand_{brand_name}"
        
        current_row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        
        if len(current_row) == 1:
            keyboard_buttons.append(current_row)
            current_row = []

    if current_row:
        keyboard_buttons.append(current_row)

    keyboard_buttons.append(
        [InlineKeyboardButton(text="⬅️ В головне меню", callback_data="back_to_main_menu")]
    )
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


async def get_models_inline_keyboard(models: List[Dict]) -> InlineKeyboardMarkup:
    """
    Створює інлайн-клавіатуру з кнопками для кожної моделі.
    Кожна кнопка має назву моделі.
    """
    keyboard_buttons = []
    current_row = []
    
    # Створення кнопок для кожної моделі
    for model in models:
        model_name = model.get('Модель', 'N/A')
        model_id = model.get('model_id')
        brand_name = model.get('brand_name')

        callback_data = f"model_{brand_name}_{model_id}"
        
        current_row.append(InlineKeyboardButton(text=model_name, callback_data=callback_data))

        if len(current_row) == 1:
            keyboard_buttons.append(current_row)
            current_row = []
    
    if current_row:
        keyboard_buttons.append(current_row)

    # Додано кнопку "Назад до брендів"
    keyboard_buttons.append(
        [InlineKeyboardButton(text="⬅️ Назад до брендів", callback_data="back_to_brands")]
    )

    # Додаємо кнопку "В головне меню"
    keyboard_buttons.append(
        [InlineKeyboardButton(text="⬅️ В головне меню", callback_data="back_to_main_menu")]
    )
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


async def get_model_details_menu_keyboard(model_id: int, brand_name: str) -> InlineKeyboardMarkup:
    """
    Створює інлайн-клавіатуру для детальної інформації про модель.
    
    :param model_id: ID моделі.
    :param brand_name: Назва бренду.
    :return: Об'єкт InlineKeyboardMarkup з кнопками.
    """
    keyboard_buttons = [
        [InlineKeyboardButton(text="Опис", callback_data=f"model_details_desc_{model_id}")],
        [InlineKeyboardButton(text="Загальні характеристики", callback_data=f"model_details_general_{model_id}")],
        [InlineKeyboardButton(text="Функції", callback_data=f"model_details_functions_{model_id}")],
        [InlineKeyboardButton(text="Технічні параметри", callback_data=f"model_details_technical_{model_id}")],
        [InlineKeyboardButton(text="Монтажні параметри", callback_data=f"model_details_installation_{model_id}")]
    ]
    
    keyboard_buttons.append(
        [InlineKeyboardButton(text="⬅️ Назад до моделей", callback_data=f"back_to_models_{brand_name}")]
    )
    
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


async def get_back_to_models_keyboard(brand_name: str) -> InlineKeyboardMarkup:
    """
    Створює інлайн-клавіатуру з кнопкою "Назад до моделей".
    
    :param brand_name: Назва бренду, до якого потрібно повернутися.
    :return: Об'єкт InlineKeyboardMarkup з однією кнопкою.
    """
    callback_data = f"brand_{brand_name}"
    keyboard_buttons = [
        [InlineKeyboardButton(text=f"⬅️ Назад до моделей {brand_name}", callback_data=callback_data)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_odometer_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Повертає клавіатуру для підтвердження відправки звіту про пробіг.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✅ Надіслати в чат",
        callback_data="send_odometer_report"
    ))
    builder.row(InlineKeyboardButton(
        text="❌ Скасувати",
        callback_data="cancel_odometer_report"
    ))
    return builder.as_markup()