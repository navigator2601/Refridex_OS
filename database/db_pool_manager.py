# database/db_pool_manager.py
import logging
from typing import Optional
import asyncpg

from config import config

logger = logging.getLogger(__name__)

# Глобальний екземпляр пулу з'єднань
_pool: Optional[asyncpg.Pool] = None


async def create_db_pool() -> Optional[asyncpg.Pool]:
    """
    Створює та повертає пул асинхронних з'єднань до PostgreSQL.
    Використовує параметри з config.database_url.
    Якщо база тимчасово недоступна, повертає None і логує попередження.
    """
    global _pool
    if _pool is not None:
        return _pool

    if not config.database_url:
        logger.error("❌ DATABASE_URL не вказано у файлі конфігурації (.env)!")
        return None

    try:
        logger.info("Підключення до бази даних PostgreSQL...")
        _pool = await asyncpg.create_pool(
            dsn=config.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60,
            max_inactive_connection_lifetime=300,
        )
        logger.info("✅ Пул з'єднань PostgreSQL успішно створено.")
        return _pool
    except Exception as e:
        logger.warning(f"⚠️ Не вдалося підключитися до PostgreSQL: {e}")
        return None


async def close_db_pool() -> None:
    """Безпечно закриває всі активні з'єднання пулу."""
    global _pool
    if _pool is not None:
        logger.info("Закриття пулу з'єднань PostgreSQL...")
        await _pool.close()
        _pool = None
        logger.info("Пул з'єднань PostgreSQL закрито.")


def get_db_pool() -> Optional[asyncpg.Pool]:
    """Повертає поточний активний пул з'єднань або None."""
    return _pool

