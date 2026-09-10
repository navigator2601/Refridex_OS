# database/repositories/auth_repo.py
import logging
from typing import Any, Dict, List, Optional
import asyncpg

from database.enums import AccessLevel, AuthStatus

logger = logging.getLogger(__name__)


class AuthRepository:
    """Репозиторій для роботи з користувачами та авторизацією в схемі telethon_auth."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_superadmin: bool = False,
    ) -> Dict[str, Any]:
        """
        Отримує користувача за telegram_id або реєструє нового гостя (GUEST).
        Якщо це супер-адміністратор (is_superadmin=True), призначає рівень ADMIN (3).
        """
        default_level = AccessLevel.ADMIN if is_superadmin else AccessLevel.GUEST
        is_authorized = True if is_superadmin else False

        query = """
        INSERT INTO telethon_auth.users (
            id, username, first_name, last_name,
            access_level, is_authorized, is_active,
            created_at, registered_at, updated_at, last_activity
        )
        VALUES (
            $1, $2, $3, $4,
            $5, $6, TRUE,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (id) DO UPDATE
        SET username = COALESCE(EXCLUDED.username, telethon_auth.users.username),
            first_name = COALESCE(EXCLUDED.first_name, telethon_auth.users.first_name),
            last_name = COALESCE(EXCLUDED.last_name, telethon_auth.users.last_name),
            last_activity = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP,
            access_level = CASE
                WHEN $7 = TRUE THEN 3
                ELSE telethon_auth.users.access_level
            END,
            is_authorized = CASE
                WHEN $7 = TRUE THEN TRUE
                ELSE telethon_auth.users.is_authorized
            END
        RETURNING *;
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                telegram_id,
                username,
                first_name,
                last_name,
                default_level.value,
                is_authorized,
                is_superadmin,
            )
            user_data = dict(row) if row else {}

            # Синхронізація з user_access_levels для уникнення розбіжностей
            if user_data:
                await self._sync_user_access_levels(conn, telegram_id, user_data.get("access_level", 0))

            return user_data

    async def get_user_by_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Отримує профіль користувача за Telegram ID."""
        query = "SELECT * FROM telethon_auth.users WHERE id = $1;"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, telegram_id)
            return dict(row) if row else None

    async def get_user_by_call_sign(self, call_sign: str) -> Optional[Dict[str, Any]]:
        """Пошук користувача за його позивним (наприклад, IM-5)."""
        if not call_sign or not call_sign.strip():
            return None
        query = "SELECT * FROM telethon_auth.users WHERE call_sign = $1;"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, call_sign.strip())
            return dict(row) if row else None

    async def update_last_activity(self, telegram_id: int) -> None:
        """Оновлює час останньої активності користувача."""
        query = """
        UPDATE telethon_auth.users
        SET last_activity = CURRENT_TIMESTAMP
        WHERE id = $1;
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, telegram_id)

    async def update_access_level(
        self,
        user_id: int,
        new_level: int,
        changed_by_user_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Змінює рівень доступу користувача з фіксацією в журналі аудиту
        та синхронізацією user_access_levels у транзакції.
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # 1. Отримуємо поточний рівень доступу
                old_row = await conn.fetchrow(
                    "SELECT access_level FROM telethon_auth.users WHERE id = $1 FOR UPDATE;",
                    user_id,
                )
                if not old_row:
                    logger.warning(f"Користувача з ID {user_id} не знайдено для зміни ролі.")
                    return False

                old_level = old_row["access_level"]
                is_authorized = (new_level > AccessLevel.GUEST)

                # 2. Оновлюємо таблицю users
                await conn.execute(
                    """
                    UPDATE telethon_auth.users
                    SET access_level = $2,
                        is_authorized = $3,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1;
                    """,
                    user_id,
                    new_level,
                    is_authorized,
                )

                # 3. Записуємо зміну в журнал аудиту (access_level_history)
                await conn.execute(
                    """
                    INSERT INTO telethon_auth.access_level_history (
                        user_id, old_access_level, new_access_level, changed_by_user_id, reason, changed_at
                    )
                    VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP);
                    """,
                    user_id,
                    old_level,
                    new_level,
                    changed_by_user_id,
                    reason or "Зміна прав адміністратором",
                )

                # 4. Синхронізуємо таблицю user_access_levels
                await self._sync_user_access_levels(conn, user_id, new_level, changed_by_user_id)

                logger.info(
                    f"Рівень доступу для user_id={user_id} змінено з {old_level} на {new_level} "
                    f"(змінив: {changed_by_user_id})"
                )
                return True

    async def update_profile(
        self,
        user_id: int,
        call_sign: Optional[str] = None,
        phone: Optional[str] = None,
        surname: Optional[str] = None,
        official_name: Optional[str] = None,
        patronymic: Optional[str] = None,
    ) -> bool:
        """Оновлює персональні дані монтажника/користувача."""
        # Уникаємо порожніх рядків для call_sign, щоб не порушувати UNIQUE обмеження
        clean_call_sign = call_sign.strip() if call_sign and call_sign.strip() else None

        query = """
        UPDATE telethon_auth.users
        SET call_sign = COALESCE($2, call_sign),
            phone = COALESCE($3, phone),
            surname = COALESCE($4, surname),
            official_name = COALESCE($5, official_name),
            patronymic = COALESCE($6, patronymic),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1;
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                query, user_id, clean_call_sign, phone, surname, official_name, patronymic
            )
            return "UPDATE 1" in result

    async def log_auth_attempt(
        self,
        user_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        session_id: Optional[int] = None,
        status: str = AuthStatus.SUCCESS.value,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Логування спроби авторизації в telethon_auth.auth_log."""
        query = """
        INSERT INTO telethon_auth.auth_log (
            user_id, phone_number, session_id, auth_status, error_message, ip_address, attempted_at
        )
        VALUES ($1, $2, $3, $4, $5, $6::inet, CURRENT_TIMESTAMP);
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query, user_id, phone_number, session_id, status, error_message, ip_address
                )
        except Exception as e:
            logger.error(f"Не вдалося записати auth_log: {e}")

    async def get_all_users(
        self, limit: int = 50, offset: int = 0, min_access_level: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Отримує список користувачів з пагінацією та фільтром за рівнем доступу."""
        if min_access_level is not None:
            query = """
            SELECT * FROM telethon_auth.users
            WHERE access_level >= $3
            ORDER BY last_activity DESC NULLS LAST
            LIMIT $1 OFFSET $2;
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, limit, offset, min_access_level)
                return [dict(r) for r in rows]
        else:
            query = """
            SELECT * FROM telethon_auth.users
            ORDER BY last_activity DESC NULLS LAST
            LIMIT $1 OFFSET $2;
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, limit, offset)
                return [dict(r) for r in rows]

    async def get_allowed_chats(self) -> List[Dict[str, Any]]:
        """Отримує список дозволених чатів для роботи Telethon."""
        query = "SELECT * FROM telethon_auth.allowed_chats WHERE is_allowed = TRUE;"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(r) for r in rows]

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Отримує список активних авторизованих сесій Telethon."""
        query = "SELECT * FROM telethon_auth.sessions WHERE is_active = TRUE AND is_authorized = TRUE;"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(r) for r in rows]

    async def _sync_user_access_levels(
        self,
        conn: asyncpg.Connection,
        user_id: int,
        access_level: int,
        updated_by_user_id: Optional[int] = None,
    ) -> None:
        """Внутрішній метод синхронізації таблиці user_access_levels."""
        can_manage_users = (access_level >= AccessLevel.ADMIN)
        can_manage_chats = (access_level >= AccessLevel.MODERATOR)
        can_manage_sessions = (access_level >= AccessLevel.ADMIN)

        sync_sql = """
        INSERT INTO telethon_auth.user_access_levels (
            user_id, access_level, can_manage_sessions, can_manage_chats, can_manage_users,
            created_at, updated_at, updated_by_user_id
        )
        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, $6)
        ON CONFLICT (user_id) DO UPDATE
        SET access_level = EXCLUDED.access_level,
            can_manage_sessions = EXCLUDED.can_manage_sessions,
            can_manage_chats = EXCLUDED.can_manage_chats,
            can_manage_users = EXCLUDED.can_manage_users,
            updated_at = CURRENT_TIMESTAMP,
            updated_by_user_id = EXCLUDED.updated_by_user_id;
        """
        try:
            await conn.execute(
                sync_sql,
                user_id,
                access_level,
                can_manage_sessions,
                can_manage_chats,
                can_manage_users,
                updated_by_user_id,
            )
        except Exception as e:
            logger.debug(f"Не вдалося синхронізувати user_access_levels: {e}")

