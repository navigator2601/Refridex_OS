# handlers/admin/chat_matrix_handlers.py
"""
Обробники для управління матрицею дозволених чатів.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Optional, Any

# ===== ОНОВЛЕНІ ІМПОРТИ =====
from database.telethon_auth_db import (
    add_allowed_chat,
    get_all_allowed_chats,
    get_allowed_chat,
    remove_allowed_chat
)
# =============================

from database.db_pool_manager import get_db_pool
from keyboards.callback_factories import AdminCallback, ChatListCallback, ChatInfoCallback
from telegram_client_module.telethon_client import TelethonClientManager

logger = logging.getLogger(__name__)

router = Router()