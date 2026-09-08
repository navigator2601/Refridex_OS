# middlewares/db_middleware.py
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineQuery, ChatMemberUpdated
from asyncpg import Pool

logger = logging.getLogger(__name__)

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        logger.info("DbSessionMiddleware ініціалізовано.")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any] # data ПОВИННА БУТИ СЛОВНИКОМ
    ) -> Any:
        logger.debug(f"DbSessionMiddleware: Обробка події типу {type(event).__name__}")

        dispatcher_obj = data.get("dispatcher")
        if not dispatcher_obj:
            logger.error("DbSessionMiddleware: Об'єкт 'dispatcher' не знайдено в data.")
            return await handler(event, data) # Передаємо data як словник

        db_pool: Pool = dispatcher_obj.workflow_data.get('db_pool')

        if not db_pool:
            logger.error("DbSessionMiddleware: 'db_pool' не знайдено в dispatcher.workflow_data. Це може бути помилкою ініціалізації.")
            return await handler(event, data) # Передаємо data як словник

        # Додаємо db_pool до існуючого словника data
        data["db_pool"] = db_pool
        logger.debug("DbSessionMiddleware: Додано 'db_pool' до 'data'.")

        user_id = None
        username = None
        first_name = None
        last_name = None

        if isinstance(event, Message):
            user_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name
        elif isinstance(event, InlineQuery):
            user_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name
        elif isinstance(event, ChatMemberUpdated):
            if event.from_user:
                user_id = event.from_user.id
                username = event.from_user.username
                first_name = event.from_user.first_name
                last_name = event.from_user.last_name
            else:
                logger.debug(f"DbSessionMiddleware: ChatMemberUpdated без from_user.")
                return await handler(event, data) # Передаємо data як словник
        else:
            logger.debug(f"DbSessionMiddleware: Подія {event.__class__.__name__} не має прямого 'from_user'. Пропускаємо обробку користувача.")
            return await handler(event, data) # Передаємо data як словник

        if user_id:
            try:
                async with db_pool.acquire() as conn:
                    async with conn.transaction():
                        await conn.execute(
                            """
                            INSERT INTO telethon_auth.users (id, username, first_name, last_name, last_activity)
                            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                            ON CONFLICT (id) DO UPDATE
                            SET username = COALESCE(EXCLUDED.username, telethon_auth.users.username),
                                first_name = COALESCE(EXCLUDED.first_name, telethon_auth.users.first_name),
                                last_name = COALESCE(EXCLUDED.last_name, telethon_auth.users.last_name),
                                last_activity = CURRENT_TIMESTAMP;
                            """,
                            user_id, username, first_name, last_name
                        )
                        logger.debug(f"DbSessionMiddleware: Дані користувача {user_id} оновлено/вставлено.")
            except Exception as e:
                logger.warning(f"DbSessionMiddleware: Не вдалося оновити активність користувача {user_id}: {e}")

            return await handler(event, data)
        else:
            return await handler(event, data) # Передаємо data як словник