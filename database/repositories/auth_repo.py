# database/repositories/auth_repo.py
import logging
from typing import Any, Dict, List, Optional
import asyncpg

from database.models.user import AccessLevel, AuthStatusEnum, UserModel

logger = logging.getLogger(__name__)


class AuthRepository:
    """
    Репозиторій для роботи з користувачами та правами доступу
    в оновленій схемі telethon_auth.
    """

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_superadmin: bool = False,
    ) -> UserModel:
        """
        Отримує користувача за Telegram ID або реєструє нового гостя (GUEST).
        Якщо це супер-адміністратор (is_superadmin=True), призначає ADMIN (3).
        """
        default_level = AccessLevel.AWAKENED.value if is_superadmin else AccessLevel.GUEST.value
        is_authorized = True if is_superadmin else False
        can_manage = True if is_superadmin else False

        query = """
        INSERT INTO telethon_auth.users (
            id, username, first_name, last_name,
            access_level, is_authorized, is_active,
            can_manage_sessions, can_manage_chats, can_manage_users,
            created_at, registered_at, updated_at, last_activity
        )
        VALUES (
            $1, $2, $3, $4,
            $5, $6, TRUE,
            $7, $7, $7,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (id) DO UPDATE
        SET username = COALESCE(EXCLUDED.username, telethon_auth.users.username),
            first_name = COALESCE(EXCLUDED.first_name, telethon_auth.users.first_name),
            last_name = COALESCE(EXCLUDED.last_name, telethon_auth.users.last_name),
            last_activity = CURRENT_TIMESTAMP,
            access_level = CASE
                WHEN $8 = TRUE THEN 101
                ELSE telethon_auth.users.access_level
            END,
            is_authorized = CASE
                WHEN $8 = TRUE THEN TRUE
                ELSE telethon_auth.users.is_authorized
            END,
            can_manage_sessions = CASE WHEN $8 = TRUE THEN TRUE ELSE telethon_auth.users.can_manage_sessions END,
            can_manage_chats = CASE WHEN $8 = TRUE THEN TRUE ELSE telethon_auth.users.can_manage_chats END,
            can_manage_users = CASE WHEN $8 = TRUE THEN TRUE ELSE telethon_auth.users.can_manage_users END
        RETURNING *;
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                telegram_id,
                username,
                first_name,
                last_name,
                default_level,
                is_authorized,
                can_manage,
                is_superadmin,
            )
            return UserModel.model_validate(dict(row))

    async def get_user_by_id(self, telegram_id: int) -> Optional[UserModel]:
        """Отримує профіль користувача за його Telegram ID."""
        query = "SELECT * FROM telethon_auth.users WHERE id = $1;"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, telegram_id)
            return UserModel.model_validate(dict(row)) if row else None

    async def get_user_by_call_sign(self, call_sign: str) -> Optional[UserModel]:
        """Пошук користувача за його робочим позивним (напр. ІМ-5)."""
        if not call_sign or not call_sign.strip():
            return None
        query = "SELECT * FROM telethon_auth.users WHERE call_sign = $1;"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, call_sign.strip())
            return UserModel.model_validate(dict(row)) if row else None

    async def update_last_activity(self, telegram_id: int) -> None:
        """Фіксація часу останньої активності користувача."""
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
        Зміна рівня доступу користувача з фіксацією в таблиці telethon_auth.access_level_history.
        """
        if not (0 <= new_level <= 101):
            raise ValueError(f"Недопустимий рівень доступу: {new_level}. Дозволено 0..101.")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # 1. Отримуємо поточний рівень доступу
                old_row = await conn.fetchrow(
                    "SELECT access_level FROM telethon_auth.users WHERE id = $1 FOR UPDATE;",
                    user_id,
                )
                if not old_row:
                    logger.warning(f"Користувача з ID {user_id} не знайдено.")
                    return False

                old_level = old_row["access_level"]
                is_authorized = (new_level > AccessLevel.GUEST)
                can_manage_users = (new_level >= AccessLevel.CORE_ADMIN)
                can_manage_chats = (new_level >= AccessLevel.PROTOCOL_LEAD)
                can_manage_sessions = (new_level >= AccessLevel.SYSTEM_ARCHITECT)

                # 2. Оновлюємо користувача
                await conn.execute(
                    """
                    UPDATE telethon_auth.users
                    SET access_level = $2,
                        is_authorized = $3,
                        can_manage_users = $4,
                        can_manage_chats = $5,
                        can_manage_sessions = $6
                    WHERE id = $1;
                    """,
                    user_id,
                    new_level,
                    is_authorized,
                    can_manage_users,
                    can_manage_chats,
                    can_manage_sessions,
                )

                # 3. Додаємо запис у журнал аудиту (access_level_history)
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
                    reason or "Зміна прав доступу",
                )

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
        """
        Оновлення персональних даних монтажника.
        Захищає call_sign від збереження порожніх рядків (зберігає NULL).
        """
        clean_call_sign = call_sign.strip() if call_sign and call_sign.strip() else None

        query = """
        UPDATE telethon_auth.users
        SET call_sign = COALESCE($2, call_sign),
            phone = COALESCE($3, phone),
            surname = COALESCE($4, surname),
            official_name = COALESCE($5, official_name),
            patronymic = COALESCE($6, patronymic)
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
        status: AuthStatusEnum = AuthStatusEnum.SUCCESS,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Логування спроби входу/авторизації в telethon_auth.auth_log."""
        query = """
        INSERT INTO telethon_auth.auth_log (
            user_id, phone_number, session_id, auth_status, error_message, ip_address, attempted_at
        )
        VALUES ($1, $2, $3, $4::telethon_auth.auth_status_enum, $5, $6::inet, CURRENT_TIMESTAMP);
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query, user_id, phone_number, session_id, status.value, error_message, ip_address
                )
        except Exception as e:
            logger.error(f"Не вдалося записати лог авторизації (auth_log): {e}")

    async def get_all_users(
        self, limit: int = 50, offset: int = 0, min_access_level: Optional[int] = None
    ) -> List[UserModel]:
        """Отримує список користувачів з пагінацією та фільтрацією за рівнем доступу."""
        if min_access_level is not None:
            query = """
            SELECT * FROM telethon_auth.users
            WHERE access_level >= $3
            ORDER BY last_activity DESC NULLS LAST
            LIMIT $1 OFFSET $2;
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, limit, offset, min_access_level)
                return [UserModel.model_validate(dict(r)) for r in rows]
        else:
            query = """
            SELECT * FROM telethon_auth.users
            ORDER BY last_activity DESC NULLS LAST
            LIMIT $1 OFFSET $2;
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, limit, offset)
                return [UserModel.model_validate(dict(r)) for r in rows]

