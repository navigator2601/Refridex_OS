# config.py

import os
from dotenv import load_dotenv
import logging

# Завантажуємо змінні з файлу .env.
# Цей виклик є безпечним і завантажить змінні, якщо вони ще не були завантажені.
load_dotenv()
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        # --- Налаштування Telegram Bot API ---
        self.bot_token = os.getenv('BOT_TOKEN')

        # Налаштування бази даних PostgreSQL
        self.database_url = os.getenv('DATABASE_URL')

        # Ключ API для OpenWeatherMap або аналогічного сервісу
        self.weather_api_key = os.getenv('WEATHER_API_KEY')

        # Налаштування Telethon API (для взаємодії з Telegram як користувач)
        # Обробляємо ValueError, якщо значення не є числом.
        try:
            self.api_id = int(os.getenv('API_ID', '0'))
        except ValueError:
            self.api_id = 0 # Встановлюємо 0, якщо не вдалося конвертувати в int
            logger.warning("API_ID у файлі .env не є дійсним числом.")

        self.api_hash = os.getenv('API_HASH')
        self.telegram_phone = os.getenv('TELEGRAM_PHONE')
        
        # Додаємо явну змінну для увімкнення/вимкнення Telethon функціоналу
        self.telethon_client_enabled = os.getenv("TELETHON_CLIENT_ENABLED", "False").lower() == "true"


        # ID адміністратора Telegram
        try:
            self.admin_id = int(os.getenv('ADMIN_ID', '0'))
        except ValueError:
            self.admin_id = 0 # Встановлюємо 0, якщо не вдалося конвертувати в int
            logger.warning("ADMIN_ID у файлі .env не є дійсним числом.")


        # Шляхи до файлів логів
        self.logs_dir = 'logs'
        self.bot_log_file = os.path.join(self.logs_dir, 'bot.log')
        self.last_login_log_file = os.path.join(self.logs_dir, 'last_login.log')

        # Створюємо директорію для логів, якщо її немає
        os.makedirs(self.logs_dir, exist_ok=True)

        # --- Перевірка, що всі необхідні змінні завантажені та дійсні ---
        self._validate_config()

    def _validate_config(self):
        """
        Перевіряє наявність та дійсність критично важливих змінних конфігурації.
        """
        missing_vars = []

        if not self.bot_token:
            missing_vars.append('BOT_TOKEN')
        if not self.database_url:
            missing_vars.append('DATABASE_URL')
        
        # Перевірки для Telethon тільки якщо він увімкнений
        if self.telethon_client_enabled:
            if self.api_id == 0: 
                missing_vars.append('API_ID (для Telethon)')
            if not self.api_hash:
                missing_vars.append('API_HASH (для Telethon)')
            if not self.telegram_phone:
                missing_vars.append('TELEGRAM_PHONE (для Telethon)')
        
        # Admin ID часто є бажаним, але не завжди абсолютно критичним для старту
        if self.admin_id == 0:
            logger.warning("ADMIN_ID не встановлено або недійсне (значення 0). Функції адміністратора можуть не працювати.")

        if missing_vars:
            error_message = f"Один або декілька необхідних ENVIRONMENTAL variables не завантажені або недійсні: {', '.join(missing_vars)}"
            logger.critical(error_message)
            logger.critical("Перевірте ваш файл .env та переконайтеся, що всі ключі присутні та мають дійсні значення.")
            raise EnvironmentError(f"Відсутні або недійсні змінні оточення: {', '.join(missing_vars)}")

# Створюємо єдиний екземпляр класу Config, який буде імпортуватися
# Це дозволяє іншим модулям імпортувати цей об'єкт і отримати доступ до налаштувань.
config = Config()