# services/messages.py
from typing import Optional


class MessageService:
    """
    Сервіс формування, шаблонізації та генерації повідомлень бота.
    
    Забезпечує ізоляцію тексту від логіки хендлерів.
    У майбутньому сюди легко підключається генерація через LLM з жорсткими системними промтами
    або зовнішні Jinja-шаблони без зміни коду хендлерів.
    """

    def get_welcome_message(self, user_name: Optional[str] = None) -> str:
        """
        Формує привітальне повідомлення для користувача.
        
        :param user_name: Ім'я користувача Telegram.
        :return: Відформатований HTML-текст привітання.
        """
        name = user_name or "користувачу"
        return (
            f"👋 <b>Привіт, {name}!</b>\n\n"
            "Ласкаво просимо до <b>Refridex OS</b>! ❄️\n"
            "Бот успішно запущений і готовий до роботи."
        )

    def get_help_message(self) -> str:
        """Повідомлення довідки."""
        return (
            "ℹ️ <b>Довідка Refridex OS:</b>\n\n"
            "• /start — перезапуск бота та головне меню\n"
            "• /help — отримати інформацію про команди\n"
        )


# Створюємо глобальний екземпляр сервісу для зручного імпорту
messages = MessageService()

