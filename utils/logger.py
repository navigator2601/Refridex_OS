# utils/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(log_level: int = logging.INFO, log_file: str = "logs/bot.log") -> logging.Logger:
    """
    Налаштування централізованого логера з виведенням у консоль та ротацією у файл.
    """
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    log_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Консольний обробник
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(log_level)

    # Файловий обробник із ротацією (до 5 МБ, зберігати 3 резервні копії)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(log_level)

    # Кореневий логер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Очищення старих обробників, щоб уникнути дублювання
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    # Зниження шумності сторонніх бібліотек
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)

    return root_logger

