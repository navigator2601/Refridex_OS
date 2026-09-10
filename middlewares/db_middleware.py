# middlewares/db_middleware.py
import logging
from typing import Any, Awaitable, Callable, Dict, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
import asyncpg

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware для прокидання пулу з'єднань PostgreSQL (asyncpg.Pool)
    у контекст кожного хендлера aiogram.
    
    Дозволяє хендлерам та сервісам отримувати з'єднання з БД через:
    `db_pool: asyncpg.Pool = data["db_pool"]`
    """

    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        super().__init__()
        self.pool = pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Прокидаємо пул з'єднань у контекстні дані події
        data["db_pool"] = self.pool

        return await handler(event, data)

