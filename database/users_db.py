# database/users_db.py
"""
Адаптер сумісності: перенаправляє операції до єдиної схеми 'telethon_auth.users'.
Забезпечує цілісність даних та відсутність дублювання таблиць користувачів.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timezone
import asyncpg

from .telethon_auth_db import (
    get_user_by_id,
    create_user,
    update_user,
    get_user_access_level,
    set_user_access_level,
    get_all_users as _get_all_users
)

logger = logging.getLogger(__name__)


async def get_user(db_pool: asyncpg.Pool, user_id: int) -> Optional[Dict]:
    """Отримує користувача з telethon_auth.users за ID."""
    return await get_user_by_id(db_pool, user_id)


async def add_user(
    db_pool: asyncpg.Pool,
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str]
) -> None:
    """Додає нового користувача або оновлює існуючого в telethon_auth.users."""
    success = await create_user(
        db_pool,
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        access_level=0,
        is_authorized=True
    )
    if not success:
        # Якщо вже існує — оновлюємо дані
        await update_user(
            db_pool,
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            last_activity=datetime.now(timezone.utc)
        )


async def update_user_activity(db_pool: asyncpg.Pool, user_id: int) -> None:
    """Оновлює час останньої активності користувача."""
    await update_user(db_pool, user_id, last_activity=datetime.now(timezone.utc))


async def is_user_authorized(db_pool: asyncpg.Pool, user_id: int) -> bool:
    """Перевіряє, чи користувач авторизований."""
    user = await get_user_by_id(db_pool, user_id)
    if user:
        return bool(user.get('is_authorized', False))
    return False


async def get_all_users(db_pool: asyncpg.Pool) -> List[Dict]:
    """Отримує список усіх користувачів."""
    return await _get_all_users(db_pool)


async def update_user_authorization_status(db_pool: asyncpg.Pool, user_id: int, is_authorized: bool) -> None:
    """Оновлює статус авторизації користувача."""
    await update_user(db_pool, user_id, is_authorized=is_authorized)


async def update_user_access_level(db_pool: asyncpg.Pool, user_id: int, new_level: int) -> None:
    """Оновлює рівень доступу користувача."""
    await set_user_access_level(db_pool, user_id, new_level)