# handlers/admin.py
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message
import asyncpg

from database.models.user import UserModel, AccessLevel
from database.repositories.auth_repo import AuthRepository
from filters.role_filter import RoleFilter
from utils.messages import AdminMessages

logger = logging.getLogger(__name__)

router = Router(name="admin_router")
# Захист усього роутера фільтром мінімального рівня CORE_ADMIN (L10)
router.message.filter(RoleFilter(min_level=AccessLevel.CORE_ADMIN))


@router.message(F.text.in_({"⚙️ Адміністрування", "⚙️ Адмін-панель"}))
async def handle_admin_panel(message: Message, user: UserModel, db_pool: asyncpg.Pool) -> None:
    """Головна панель керування адміністратора."""
    total_users = 0
    active_sessions = 0
    allowed_chats_count = 0

    if db_pool:
        async with db_pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM telethon_auth.users") or 0
            active_sessions = await conn.fetchval(
                "SELECT COUNT(*) FROM telethon_auth.sessions WHERE is_active = true AND is_authorized = true"
            ) or 0
            allowed_chats_count = await conn.fetchval(
                "SELECT COUNT(*) FROM telethon_auth.allowed_chats WHERE is_allowed = true"
            ) or 0

    text = AdminMessages.panel_stats(
        total_users=total_users,
        active_sessions=active_sessions,
        allowed_chats=allowed_chats_count,
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📝 Додати або редагувати дані")
async def handle_edit_data(message: Message, user: UserModel) -> None:
    """Розділ внесення та редагування нормативних даних."""
    await message.answer(
        "📝 <b>Керування та редагування даних [L10]</b>\n\n"
        "Доступні розділи редагування:\n"
        "• 📍 Реєстр торговельних точок (ТТ)\n"
        "• ❄️ Моделі кондиціонерів та норми фреону\n"
        "• 👥 Призначення прав та позивних монтажників",
        parse_mode="HTML",
    )


@router.message(F.text == "👥 Керування користувачами")
async def handle_manage_users(message: Message, user: UserModel, db_pool: asyncpg.Pool) -> None:
    """Список та статус користувачів."""
    users = []
    if db_pool:
        async with db_pool.acquire() as conn:
            users = await conn.fetch(
                """
                SELECT id, username, surname, official_name, call_sign, access_level, is_authorized
                FROM telethon_auth.users
                ORDER BY access_level DESC, registered_at DESC
                LIMIT 10
                """
            )

    if not users:
        await message.answer(AdminMessages.USERS_LIST_EMPTY)
        return

    text = AdminMessages.users_list(users)
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🤖 Telethon сесії")
async def handle_telethon_sessions(message: Message, user: UserModel, db_pool: asyncpg.Pool) -> None:
    """Перегляд активних MTProto-сесій Telethon."""
    sessions = []
    if db_pool:
        async with db_pool.acquire() as conn:
            sessions = await conn.fetch(
                """
                SELECT id, phone_number, is_authorized, is_active, last_login, telegram_username
                FROM telethon_auth.sessions
                ORDER BY created_at DESC
                """
            )

    if not sessions:
        await message.answer(AdminMessages.SESSIONS_LIST_EMPTY)
        return

    text = AdminMessages.sessions_list(sessions)
    await message.answer(text, parse_mode="HTML")
