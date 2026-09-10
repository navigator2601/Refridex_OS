# middlewares/auth_middleware.py
import logging
from typing import Any, Awaitable, Callable, Dict, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
import asyncpg

from config import config
from database.models.user import UserModel
from database.repositories.auth_repo import AuthRepository

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """
    Middleware контролю доступу (RBAC).
    
    Для кожної вхідної події:
    1. Перехоплює Telegram User ID (event_from_user).
    2. Отримує або реєструє користувача в telethon_auth.users.
    3. Автоматично призначає статус ADMIN для ADMIN_ID з конфігурації.
    4. Прокидає об'єкт `user: UserModel` та `auth_repo: AuthRepository`
       у контекст кожного хендлера:
       `user: UserModel = data["user"]`
    """

    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        super().__init__()
        self.pool = pool
        self.auth_repo = AuthRepository(pool) if pool else None

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_user: Optional[User] = data.get("event_from_user")

        if event_user and not event_user.is_bot:
            is_superadmin = (event_user.id == config.admin_id)
            user_model = None

            if self.auth_repo:
                try:
                    user_model = await self.auth_repo.get_or_create_user(
                        telegram_id=event_user.id,
                        username=event_user.username,
                        first_name=event_user.first_name,
                        last_name=event_user.last_name,
                        is_superadmin=is_superadmin,
                    )
                except Exception as e:
                    logger.error(f"Помилка в AuthMiddleware для користувача {event_user.id}: {e}")

            if user_model is None:
                # Резервна модель при тимчасовій недоступності БД
                user_model = UserModel(
                    id=event_user.id,
                    username=event_user.username,
                    first_name=event_user.first_name,
                    last_name=event_user.last_name,
                    access_level=AccessLevel.AWAKENED if is_superadmin else AccessLevel.GUEST,
                    is_authorized=is_superadmin,
                    can_manage_sessions=is_superadmin,
                    can_manage_chats=is_superadmin,
                    can_manage_users=is_superadmin,
                )

            data["user"] = user_model
            data["auth_repo"] = self.auth_repo

        return await handler(event, data)


