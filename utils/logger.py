# utils/logger.py
import datetime
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from config import config


class RefridexFormatter(logging.Formatter):
    """Кастомний форматер для гарного та інформативного відображення логів."""

    def formatTime(self, record, datefmt=None):
        dt = datetime.datetime.fromtimestamp(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{int(record.msecs):03d}"

    FORMATS = {
        logging.DEBUG: "[Refridex OS • DEBUG • %(asctime)s] 🐞 %(name)s: %(message)s",
        logging.INFO: "[Refridex OS • INFO • %(asctime)s] 🔹 %(name)s: %(message)s",
        logging.WARNING: "[Refridex OS • УВАГА • %(asctime)s] ⚠️ %(name)s: %(message)s",
        logging.ERROR: "[Refridex OS • ПОМИЛКА • %(asctime)s] ❌ %(name)s: %(message)s",
        logging.CRITICAL: "[Refridex OS • КРИТИЧНО • %(asctime)s] 💥 %(name)s: %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt)
        formatter.formatTime = self.formatTime
        return formatter.format(record)


def setup_logging() -> None:
    """Ініціалізація консольного та файлового логування."""
    os.makedirs(config.logs_dir, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = RefridexFormatter()

    # Консольний вивід
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Файловий вивід з ротацією щодня
    file_handler = TimedRotatingFileHandler(
        config.bot_log_file,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Зменшення шуму від сторонніх бібліотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    logging.getLogger(__name__).info("Систему логування налаштовано.")

