# database/telethon_auth_db.py
"""
Модуль для управління схемою 'telethon_auth'.
Основні операції: управління користувачами, сесіями, дозволами та журналами.
"""

import asyncpg
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# ФУНКЦІЇ ДЛЯ УПРАВЛІННЯ КОРИСТУВАЧАМИ (telethon_auth.users)
# ============================================================================

async def get_user_by_id(pool: asyncpg.Pool, user_id: int) -> Optional[Dict]:
    """
    Отримує користувача за ID.
    
    Args:
        pool: пул подключений до БД
        user_id: Telegram User ID
        
    Returns:
        Словник з даними користувача або None
    """
    async with pool.acquire() as conn:
        try:
            record = await conn.fetchrow(
                "SELECT * FROM telethon_auth.users WHERE id = $1",
                user_id
            )
            if record:
                logger.info(f"✅ Користувач {user_id} знайдений у БД.")
                return dict(record)
            else:
                logger.info(f"⚠️ Користувач {user_id} не знайдений у БД.")
                return None
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні користувача {user_id}: {e}", exc_info=True)
            return None


async def create_user(
    pool: asyncpg.Pool,
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    call_sign: Optional[str] = None,
    access_level: int = 0,
    is_authorized: bool = False
) -> bool:
    """
    Створює нового користувача у БД.
    
    Args:
        pool: пул подключений до БД
        user_id: Telegram User ID
        username: username користувача
        first_name: ім'я користувача
        last_name: прізвище користувача
        call_sign: позивний/внутрішнє імя
        access_level: рівень доступу (за умовчанням 0 = GUEST)
        is_authorized: чи авторизований користувач
        
    Returns:
        True якщо успішно, False якщо помилка або користувач вже існує
    """
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO telethon_auth.users 
                (id, username, first_name, last_name, call_sign, access_level, is_authorized)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO NOTHING;
            """, user_id, username, first_name, last_name, call_sign, access_level, is_authorized)
            
            logger.info(f"✅ Користувач {user_id} ({username}) успішно додан до БД.")
            return True
        except asyncpg.UniqueViolationError:
            logger.warning(f"⚠️ Користувач {user_id} вже існує у БД.")
            return False
        except Exception as e:
            logger.error(f"❌ Помилка при додаванні користувача {user_id}: {e}", exc_info=True)
            return False


async def update_user(
    pool: asyncpg.Pool,
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    call_sign: Optional[str] = None,
    access_level: Optional[int] = None,
    is_authorized: Optional[bool] = None,
    last_activity: Optional[datetime] = None
) -> bool:
    """
    Оновлює дані користувача.
    
    Args:
        pool: пул подключений до БД
        user_id: Telegram User ID
        username: username користувача
        first_name: ім'я користувача
        last_name: прізвище користувача
        call_sign: позивний/внутрішнє імя
        access_level: рівень доступу
        is_authorized: чи авторизований користувач
        last_activity: час останньої активності
        
    Returns:
        True якщо успішно, False якщо помилка
    """
    async with pool.acquire() as conn:
        try:
            # Будуємо динамічний UPDATE запит
            updates = []
            params = [user_id]
            param_count = 1
            
            if username is not None:
                param_count += 1
                updates.append(f"username = ${param_count}")
                params.append(username)
            
            if first_name is not None:
                param_count += 1
                updates.append(f"first_name = ${param_count}")
                params.append(first_name)
            
            if last_name is not None:
                param_count += 1
                updates.append(f"last_name = ${param_count}")
                params.append(last_name)
            
            if call_sign is not None:
                param_count += 1
                updates.append(f"call_sign = ${param_count}")
                params.append(call_sign)
            
            if access_level is not None:
                param_count += 1
                updates.append(f"access_level = ${param_count}")
                params.append(access_level)
            
            if is_authorized is not None:
                param_count += 1
                updates.append(f"is_authorized = ${param_count}")
                params.append(is_authorized)
            
            if last_activity is not None:
                param_count += 1
                updates.append(f"last_activity = ${param_count}")
                params.append(last_activity)
            
            if not updates:
                logger.warning(f"⚠️ Немає даних для оновлення користувача {user_id}.")
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"""
                UPDATE telethon_auth.users 
                SET {', '.join(updates)}
                WHERE id = $1
            """
            
            await conn.execute(query, *params)
            logger.info(f"✅ Користувач {user_id} успішно оновлений.")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка при оновленні користувача {user_id}: {e}", exc_info=True)
            return False


async def get_user_access_level(pool: asyncpg.Pool, user_id: int) -> int:
    """
    Отримує рівень доступу користувача.
    
    Args:
        pool: пул подключений до БД
        user_id: Telegram User ID
        
    Returns:
        Рівень доступу (0, 1, 2, 3) або 0 якщо користувач не знайден
    """
    async with pool.acquire() as conn:
        try:
            record = await conn.fetchval(
                "SELECT access_level FROM telethon_auth.users WHERE id = $1",
                user_id
            )
            level = record if record is not None else 0
            logger.info(f"✅ Рівень доступу користувача {user_id}: {level}")
            return level
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні рівня доступу {user_id}: {e}", exc_info=True)
            return 0


async def set_user_access_level(
    pool: asyncpg.Pool,
    user_id: int,
    access_level: int,
    changed_by_user_id: Optional[int] = None,
    reason: Optional[str] = None
) -> bool:
    """
    Встановлює рівень доступу користувача и записує у журнал.
    
    Args:
        pool: пул подключений до БД
        user_id: Telegram User ID
        access_level: новий рівень доступу
        changed_by_user_id: ID користувача, який змінив доступ
        reason: причина зміни
        
    Returns:
        True якщо успішно, False якщо помилка
    """
    async with pool.acquire() as conn:
        try:
            # Отримуємо старий рівень
            old_level = await conn.fetchval(
                "SELECT access_level FROM telethon_auth.users WHERE id = $1",
                user_id
            )
            
            # Оновлюємо рівень доступу
            await conn.execute(
                "UPDATE telethon_auth.users SET access_level = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                access_level, user_id
            )
            
            # Записуємо у журнал
            await conn.execute("""
                INSERT INTO telethon_auth.access_level_history 
                (user_id, old_access_level, new_access_level, changed_by_user_id, reason)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, old_level, access_level, changed_by_user_id, reason)
            
            logger.info(f"✅ Рівень доступу користувача {user_id} змінено з {old_level} на {access_level}.")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка при встановленні рівня доступу {user_id}: {e}", exc_info=True)
            return False


async def get_all_users(pool: asyncpg.Pool) -> List[Dict]:
    """
    Отримує всіх користувачів.
    
    Returns:
        Список зі словниками користувачів
    """
    async with pool.acquire() as conn:
        try:
            records = await conn.fetch("SELECT * FROM telethon_auth.users ORDER BY created_at DESC")
            logger.info(f"✅ Отримано {len(records)} користувачів.")
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні всіх користувачів: {e}", exc_info=True)
            return []


# ============================================================================
# ФУНКЦІЇ ДЛЯ УПРАВЛІННЯ СЕСІЯМИ (telethon_auth.sessions)
# ============================================================================

async def save_telethon_session(
    pool: asyncpg.Pool,
    phone_number: str,
    session_string: str,
    api_id: int,
    api_hash: str,
    user_id: Optional[int] = None,
    is_authorized: bool = True,
    telegram_user_id: Optional[int] = None,
    telegram_username: Optional[str] = None,
    telegram_first_name: Optional[str] = None,
    telegram_last_name: Optional[str] = None
) -> bool:
    """
    Зберігає або оновлює сесію Telethon.
    
    Args:
        pool: пул подключений до БД
        phone_number: номер телефону
        session_string: сесійний рядок
        api_id: API ID
        api_hash: API Hash
        user_id: ID користувача (опційно)
        is_authorized: чи авторизована сесія
        telegram_user_id: ID користувача у Telegram (кешовано)
        telegram_username: username у Telegram
        telegram_first_name: ім'я у Telegram
        telegram_last_name: прізвище у Telegram
        
    Returns:
        True якщо успішно, False якщо помилка
    """
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO telethon_auth.sessions 
                (phone_number, session_string, api_id, api_hash, user_id, is_authorized, 
                 telegram_user_id, telegram_username, telegram_first_name, telegram_last_name, last_login)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, CURRENT_TIMESTAMP)
                ON CONFLICT (phone_number) DO UPDATE SET
                    session_string = EXCLUDED.session_string,
                    api_id = EXCLUDED.api_id,
                    api_hash = EXCLUDED.api_hash,
                    user_id = EXCLUDED.user_id,
                    is_authorized = EXCLUDED.is_authorized,
                    telegram_user_id = EXCLUDED.telegram_user_id,
                    telegram_username = EXCLUDED.telegram_username,
                    telegram_first_name = EXCLUDED.telegram_first_name,
                    telegram_last_name = EXCLUDED.telegram_last_name,
                    last_login = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP;
            """, phone_number, session_string, api_id, api_hash, user_id, is_authorized,
                telegram_user_id, telegram_username, telegram_first_name, telegram_last_name)
            
            logger.info(f"✅ Сесія для {phone_number} успішно збережена.")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка при збереженні сесії {phone_number}: {e}", exc_info=True)
            return False


async def get_telethon_session(pool: asyncpg.Pool, phone_number: str) -> Optional[Dict]:
    """
    Отримує сесію Telethon за номером телефону.
    
    Args:
        pool: пул подключений до БД
        phone_number: номер телефону
        
    Returns:
        Словник з даними сесії або None
    """
    async with pool.acquire() as conn:
        try:
            record = await conn.fetchrow(
                "SELECT * FROM telethon_auth.sessions WHERE phone_number = $1 AND is_authorized = TRUE",
                phone_number
            )
            if record:
                logger.info(f"✅ Сесія для {phone_number} завантажена.")
                return dict(record)
            else:
                logger.info(f"⚠️ Сесія для {phone_number} не знайдена.")
                return None
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні сесії {phone_number}: {e}", exc_info=True)
            return None


async def get_user_sessions(pool: asyncpg.Pool, user_id: int) -> List[Dict]:
    """
    Отримує всі сесії користувача.
    
    Args:
        pool: пул подключений до БД
        user_id: ID користувача
        
    Returns:
        Список сесій користувача
    """
    async with pool.acquire() as conn:
        try:
            records = await conn.fetch(
                "SELECT * FROM telethon_auth.sessions WHERE user_id = $1 AND is_active = TRUE ORDER BY last_login DESC",
                user_id
            )
            logger.info(f"✅ Отримано {len(records)} сесій для користувача {user_id}.")
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні сесій користувача {user_id}: {e}", exc_info=True)
            return []


async def delete_telethon_session(pool: asyncpg.Pool, phone_number: str) -> bool:
    """
    Видаляє сесію Telethon.
    
    Args:
        pool: пул подключений до БД
        phone_number: номер телефону
        
    Returns:
        True якщо успішно, False якщо помилка
    """
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "DELETE FROM telethon_auth.sessions WHERE phone_number = $1",
                phone_number
            )
            logger.info(f"✅ Сесія для {phone_number} видалена.")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка при видаленні сесії {phone_number}: {e}", exc_info=True)
            return False


async def get_all_sessions(pool: asyncpg.Pool) -> List[Dict]:
    """
    Отримує всі авторизовані сесії.
    
    Returns:
        Список в��іх сесій
    """
    async with pool.acquire() as conn:
        try:
            records = await conn.fetch(
                "SELECT * FROM telethon_auth.sessions WHERE is_authorized = TRUE AND is_active = TRUE ORDER BY last_login DESC"
            )
            logger.info(f"✅ Отримано {len(records)} активних сесій.")
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні всіх сесій: {e}", exc_info=True)
            return []


# ============================================================================
# ФУНКЦІЇ ДЛЯ УПРАВЛІННЯ ДОЗВОЛЕНИМИ ЧАТАМИ (telethon_auth.allowed_chats)
# ============================================================================

async def add_allowed_chat(
    pool: asyncpg.Pool,
    telegram_chat_id: int,
    chat_title: str,
    chat_type: str,
    added_by_user_id: int,
    username: Optional[str] = None,
    description: Optional[str] = None
) -> bool:
    """
    Додає дозволений чат/канал.
    
    Args:
        pool: пул подключений до БД
        telegram_chat_id: ID чату у Telegram
        chat_title: назва чату
        chat_type: тип чату (private, group, supergroup, channel)
        added_by_user_id: ID користувача, який додав чат
        username: username чату
        description: опис чату
        
    Returns:
        True якщо успішно, False якщо помилка
    """
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO telethon_auth.allowed_chats 
                (telegram_chat_id, chat_title, chat_type, username, description, added_by_user_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (telegram_chat_id) DO UPDATE SET
                    chat_title = EXCLUDED.chat_title,
                    chat_type = EXCLUDED.chat_type,
                    username = EXCLUDED.username,
                    description = EXCLUDED.description,
                    updated_at = CURRENT_TIMESTAMP;
            """, telegram_chat_id, chat_title, chat_type, username, description, added_by_user_id)
            
            logger.info(f"✅ Чат '{chat_title}' ({telegram_chat_id}) додано/оновлено.")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка при додаванні чату: {e}", exc_info=True)
            return False


async def get_allowed_chat(pool: asyncpg.Pool, telegram_chat_id: int) -> Optional[Dict]:
    """
    Отримує дозволений чат за ID.
    
    Args:
        pool: пул подключений до БД
        telegram_chat_id: ID чату у Telegram
        
    Returns:
        Словник з даними чату або None
    """
    async with pool.acquire() as conn:
        try:
            record = await conn.fetchrow(
                "SELECT * FROM telethon_auth.allowed_chats WHERE telegram_chat_id = $1 AND is_allowed = TRUE",
                telegram_chat_id
            )
            if record:
                logger.info(f"✅ Дозволений чат {telegram_chat_id} знайдений.")
                return dict(record)
            return None
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні чату {telegram_chat_id}: {e}", exc_info=True)
            return None


async def get_all_allowed_chats(pool: asyncpg.Pool) -> List[Dict]:
    """
    Отримує всі дозволені чати.
    
    Returns:
        Список дозволених чатів
    """
    async with pool.acquire() as conn:
        try:
            records = await conn.fetch(
                "SELECT * FROM telethon_auth.allowed_chats WHERE is_allowed = TRUE ORDER BY added_at DESC"
            )
            logger.info(f"✅ Отримано {len(records)} дозволених чатів.")
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"❌ Помилк�� при отриманні чатів: {e}", exc_info=True)
            return []


async def remove_allowed_chat(pool: asyncpg.Pool, telegram_chat_id: int) -> bool:
    """
    Видаляє дозволений чат (м'яке видалення).
    
    Args:
        pool: пул подключений до БД
        telegram_chat_id: ID чату у Telegram
        
    Returns:
        True якщо успішно, False якщо помилка
    """
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "UPDATE telethon_auth.allowed_chats SET is_allowed = FALSE, updated_at = CURRENT_TIMESTAMP WHERE telegram_chat_id = $1",
                telegram_chat_id
            )
            logger.info(f"✅ Чат {telegram_chat_id} видалено з дозволених.")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка при видаленні чату: {e}", exc_info=True)
            return False


# ============================================================================
# ФУНКЦІЇ ДЛЯ ЛОГУВАННЯ АВТОРИЗАЦІЇ (telethon_auth.auth_log)
# ============================================================================

async def log_auth_attempt(
    pool: asyncpg.Pool,
    user_id: Optional[int],
    phone_number: Optional[str],
    session_id: Optional[int],
    auth_status: str,
    error_message: Optional[str] = None,
    ip_address: Optional[str] = None
) -> bool:
    """
    Логує спробу авторизації.
    
    Args:
        pool: пул подключений до БД
        user_id: ID користувача
        phone_number: номер телефону
        session_id: ID сесії
        auth_status: статус авторизації (SUCCESS, FAILED, EXPIRED, REVOKED)
        error_message: повідомлення про помилку (якщо є)
        ip_address: IP адреса (якщо доступна)
        
    Returns:
        True якщо успішно, False якщо помилка
    """
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO telethon_auth.auth_log 
                (user_id, phone_number, session_id, auth_status, error_message, ip_address)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user_id, phone_number, session_id, auth_status, error_message, ip_address)
            
            logger.info(f"✅ Спроба авторизації записана: {auth_status}")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка при логуванні авторизації: {e}", exc_info=True)
            return False


async def get_auth_log(pool: asyncpg.Pool, user_id: int, limit: int = 50) -> List[Dict]:
    """
    Отримує логи авторизації користувача.
    
    Args:
        pool: пул подключений до БД
        user_id: ID користувача
        limit: кількість записів
        
    Returns:
        Список логів авторизації
    """
    async with pool.acquire() as conn:
        try:
            records = await conn.fetch(
                "SELECT * FROM telethon_auth.auth_log WHERE user_id = $1 ORDER BY attempted_at DESC LIMIT $2",
                user_id, limit
            )
            logger.info(f"✅ Отримано {len(records)} записів логу авторизації для користувача {user_id}.")
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні логу авторизації: {e}", exc_info=True)
            return []