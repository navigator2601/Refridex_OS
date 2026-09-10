# handlers/admin.py
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message
import asyncpg

from database.models.user import UserModel, AccessLevel
from database.repositories.auth_repo import AuthRepository
from filters.role_filter import RoleFilter

logger = logging.getLogger(__name__)

router = Router(name="admin_router")
# Захист усього роутера фільтром мінімального рівня ADMIN
router.message.filter(RoleFilter(min_level=AccessLevel.ADMIN))


@router.message(F.text == "⚙️ Адмін-панель")
async def handle_admin_panel(message: Message, user: UserModel, db_pool: asyncpg.Pool) -> None:
    """Головна панель керування адміністратора."""
    async with db_pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM telethon_auth.users")
        active_sessions = await conn.fetchval(
            "SELECT COUNT(*) FROM telethon_auth.sessions WHERE is_active = true AND is_authorized = true"
        )
        allowed_chats_count = await conn.fetchval(
            "SELECT COUNT(*) FROM telethon_auth.allowed_chats WHERE is_allowed = true"
        )

    text = (
        "<b>⚙️ Адміністративна панель Refridex OS</b>\n\n"
        f"<b>Статистика системи:</b>\n"
        f"• Зареєстровано користувачів: <b>{total_users or 0}</b>\n"
        f"• Активних Telethon-сесій: <b>{active_sessions or 0}</b>\n"
        f"• Дозволених робочих груп/чатів: <b>{allowed_chats_count or 0}</b>\n\n"
        "<i>Оберіть потрібну дію в меню адміністрування.</i>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "👥 Керування користувачами")
async def handle_manage_users(message: Message, user: UserModel, db_pool: asyncpg.Pool) -> None:
    """Список та статус користувачів."""
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
        await message.answer("👥 Користувачів у системі поки немає.")
        return

    lines = ["<b>👥 Останні зареєстровані користувачі:</b>\n"]
    for u in users:
        lvl = AccessLevel(u["access_level"]).badge
        name = f"{u['surname'] or ''} {u['official_name'] or ''}".strip() or (f"@{u['username']}" if u['username'] else f"ID: {u['id']}")
        call = f" [{u['call_sign']}]" if u["call_sign"] else ""
        auth = "✅" if u["is_authorized"] else "⏳"
        lines.append(f"{auth} {lvl} {name}{call} (<code>{u['id']}</code>)")

    lines.append("\n<i>Для зміни рівня доступу використовуйте команду /setrole &lt;id&gt; &lt;level&gt;</i>")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "🤖 Telethon сесії")
async def handle_telethon_sessions(message: Message, user: UserModel, db_pool: asyncpg.Pool) -> None:
    """Перегляд активних MTProto-сесій Telethon."""
    async with db_pool.acquire() as conn:
        sessions = await conn.fetch(
            """
            SELECT id, phone_number, is_authorized, is_active, last_login, telegram_username
            FROM telethon_auth.sessions
            ORDER BY created_at DESC
            """
        )

    if not sessions:
        await message.answer("🤖 Жодної Telethon-сесії ще не зареєстровано в базі.")
        return

    lines = ["<b>🤖 Реєстр MTProto-сесій Telethon:</b>\n"]
    for s in sessions:
        status = "🟢 Активна" if (s["is_authorized"] and s["is_active"]) else "🔴 Неактивна / Очікує коду"
        uname = f" (@{s['telegram_username']})" if s['telegram_username'] else ""
        lines.append(f"• <b>{s['phone_number']}</b>{uname}: {status}")

    await message.answer("\n".join(lines), parse_mode="HTML")

