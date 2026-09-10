# config.py
import logging
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Завантажуємо змінні оточення з .env
load_dotenv()
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    """Централізований типізований об'єкт конфігурації Refridex OS."""

    # Telegram Bot
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    admin_id: int = field(default_factory=lambda: int(os.getenv("ADMIN_ID", "0") or "0"))

    # PostgreSQL
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))

    # Telethon MTProto Client
    api_id: int = field(default_factory=lambda: int(os.getenv("API_ID", "0") or "0"))
    api_hash: str = field(default_factory=lambda: os.getenv("API_HASH", ""))
    telegram_phone: str = field(default_factory=lambda: os.getenv("TELEGRAM_PHONE", ""))
    telethon_client_enabled: bool = field(
        default_factory=lambda: os.getenv("TELETHON_CLIENT_ENABLED", "False").lower() in ("true", "1", "yes")
    )

    # Optional APIs
    weather_api_key: str = field(default_factory=lambda: os.getenv("WEATHER_API_KEY", ""))

    # Paths & Logging
    logs_dir: str = "logs"
    bot_log_file: str = "logs/bot.log"

    def __post_init__(self) -> None:
        """Валідація обов'язкових змінних оточення."""
        missing = []
        if not self.bot_token:
            missing.append("BOT_TOKEN")
        if not self.database_url:
            missing.append("DATABASE_URL")

        if self.telethon_client_enabled:
            if not self.api_id:
                missing.append("API_ID (для Telethon)")
            if not self.api_hash:
                missing.append("API_HASH (для Telethon)")

        if missing:
            msg = f"Критичні змінні оточення відсутні у .env: {', '.join(missing)}"
            logger.critical(msg)
            raise EnvironmentError(msg)

        if not self.admin_id:
            logger.warning("⚠️ ADMIN_ID не встановлено або дорівнює 0. Деякі адміністративні функції можуть бути обмежені.")


# Єдиний синглтон конфігурації для імпорту в модулях
config = Config()

