# database/db_pool_manager.py
"""
Менеджер пула подключень до PostgreSQL.
Управління підключенням та ініціалізацією таблиць.
"""

import asyncpg
import logging
from config import config

logger = logging.getLogger(__name__)

_db_pool = None


async def create_db_pool():
    """Створює пул з'єднань з базою даних PostgreSQL."""
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = await asyncpg.create_pool(config.database_url)
            logger.info("✅ Пул з'єднань до бази даних створено успішно.")
        except Exception as e:
            logger.critical(f"❌ Не вдалося створити пул з'єднань до БД: {e}", exc_info=True)
            raise


async def get_db_pool():
    """Повертає існуючий пул з'єднань."""
    if _db_pool is None:
        logger.warning("⚠️ Запит на пул з'єднань до БД, але він не був створений. Спроба створити.")
        await create_db_pool()
    return _db_pool


async def close_db_pool():
    """Закриває пул з'єднань з базою даних."""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
        logger.info("✅ Пул з'єднань до бази даних закрито.")


async def init_db_tables():
    """
    Ініціалізує базу даних, перевіряючи існування таблиць.
    
    Примітка: Схема telethon_auth повинна бути створена вручну через SQL DDL.
    Цей метод тільки перевіряє існування таблиць.
    """
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # ====================================================================
                # Перевірка та ініціалізація СТАРИХ таблиць (якщо вони існують)
                # ====================================================================
                
                # Таблиця public.users (СТАРА, може бути видалена пізніше)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS public.users (
                        id BIGINT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        access_level INT DEFAULT 0,
                        is_authorized BOOLEAN DEFAULT FALSE,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("✅ Таблиця 'public.users' перевірена/створена.")

                # Таблиця public.telethon_sessions (СТАРА)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS public.telethon_sessions (
                        phone_number VARCHAR(255) PRIMARY KEY,
                        session_string TEXT NOT NULL,
                        api_id INTEGER NOT NULL,
                        api_hash VARCHAR(255) NOT NULL,
                        last_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("✅ Таблиця 'public.telethon_sessions' перевірена/створена.")

                # Таблиця public.telethon_allowed_chats (СТАРА)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS public.telethon_allowed_chats (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT UNIQUE NOT NULL,
                        chat_title TEXT,
                        chat_type TEXT,
                        username TEXT,
                        added_by_user_id BIGINT,
                        added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("✅ Таблиця 'public.telethon_allowed_chats' перевірена/створена.")

                # ====================================================================
                # Перевірка схеми telethon_auth (основна)
                # ====================================================================
                
                schema_exists = await conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.schemata 
                        WHERE schema_name = 'telethon_auth'
                    )
                """)
                
                if schema_exists:
                    logger.info("✅ Схема 'telethon_auth' існує. Перевіряємо таблиці...")
                    
                    # Перевірка таблиць у схемі
                    tables = [
                        'users',
                        'sessions',
                        'allowed_chats',
                        'user_access_levels',
                        'access_level_history',
                        'auth_log'
                    ]
                    
                    for table in tables:
                        table_exists = await conn.fetchval(f"""
                            SELECT EXISTS(
                                SELECT 1 FROM information_schema.tables 
                                WHERE table_schema = 'telethon_auth' 
                                AND table_name = '{table}'
                            )
                        """)
                        
                        if table_exists:
                            logger.info(f"✅ Таблиця 'telethon_auth.{table}' існує.")
                        else:
                            logger.warning(f"⚠️ Таблиця 'telethon_auth.{table}' НЕ існує. Потрібно запустити DDL скрипт.")
                else:
                    logger.warning("⚠️ Схема 'telethon_auth' НЕ існує! Потрібно запустити database/telethon_auth_init.sql")

        logger.info("✅ Ініціалізація таблиць завершена.")

    except Exception as e:
        logger.error(f"❌ Помилка при ініціалізації таблиць: {e}", exc_info=True)
        raise