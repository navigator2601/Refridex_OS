# database/__init__.py
"""
Модуль для управління базою даних.
"""

# Імпорти з нового модуля telethon_auth_db
from .telethon_auth_db import (
    # Функції для управління користувачами
    get_user_by_id,
    create_user,
    update_user,
    get_user_access_level,
    set_user_access_level,
    get_all_users,
    
    # Функції для управління сесіями
    save_telethon_session,
    get_telethon_session,
    delete_telethon_session,
    get_user_sessions,
    get_all_sessions,
    
    # Функції для управління дозволеними чатами
    add_allowed_chat,
    get_allowed_chat,
    get_all_allowed_chats,
    remove_allowed_chat,
    
    # Функції для логування авторизації
    log_auth_attempt,
    get_auth_log,
)

# Імпорти для управління пулом подключень
from .db_pool_manager import (
    create_db_pool,
    close_db_pool,
    init_db_tables,
    get_db_pool,
)

__all__ = [
    # Користувачі
    "get_user_by_id",
    "create_user",
    "update_user",
    "get_user_access_level",
    "set_user_access_level",
    "get_all_users",
    
    # Сесії
    "save_telethon_session",
    "get_telethon_session",
    "delete_telethon_session",
    "get_user_sessions",
    "get_all_sessions",
    
    # Дозволені чати
    "add_allowed_chat",
    "get_allowed_chat",
    "get_all_allowed_chats",
    "remove_allowed_chat",
    
    # Логування авторизації
    "log_auth_attempt",
    "get_auth_log",
    
    # Пул подключень
    "create_db_pool",
    "close_db_pool",
    "init_db_tables",
    "get_db_pool",
]