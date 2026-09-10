# database/models/user.py
from datetime import datetime
from enum import Enum, IntEnum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AccessLevel(IntEnum):
    """
    Рівні доступу користувачів у системі Refridex OS.
    Відповідає CHECK ((access_level >= 0) AND (access_level <= 3)).
    """
    GUEST = 0      # Гість (без доступу до замірів)
    USER = 1       # Монтажник
    MODERATOR = 2  # Бригадир / Диспетчер
    ADMIN = 3      # Адміністратор системи

    @property
    def title(self) -> str:
        titles = {
            self.GUEST: "Гість",
            self.USER: "Монтажник",
            self.MODERATOR: "Бригадир / Диспетчер",
            self.ADMIN: "Адміністратор",
        }
        return titles.get(self, "Невідомо")

    @property
    def badge(self) -> str:
        badges = {
            self.GUEST: "👤 Гість",
            self.USER: "🔧 Монтажник",
            self.MODERATOR: "📋 Бригадир",
            self.ADMIN: "👑 Адміністратор",
        }
        return badges.get(self, "❓ Невідомо")

    def is_admin(self) -> bool:
        return self >= self.ADMIN

    def is_moderator(self) -> bool:
        return self >= self.MODERATOR

    def is_user(self) -> bool:
        return self >= self.USER


class AuthStatusEnum(str, Enum):
    """Статуси аудиту авторизації в telethon_auth.auth_log."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class UserModel(BaseModel):
    """Модель користувача з таблиці telethon_auth.users."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Telegram User ID (PK)")
    username: Optional[str] = Field(None, description="Юзернейм без @")
    call_sign: Optional[str] = Field(None, description="Робочий позивний монтажника (ІМ-5)")
    first_name: Optional[str] = Field(None, description="Ім'я з Telegram")
    last_name: Optional[str] = Field(None, description="Прізвище з Telegram")
    surname: Optional[str] = Field(None, description="Офіційне прізвище монтажника")
    official_name: Optional[str] = Field(None, description="Офіційне ім'я")
    patronymic: Optional[str] = Field(None, description="По батькові")
    phone: Optional[str] = Field(None, description="Робочий номер телефону")

    is_authorized: bool = Field(default=False, description="Чи авторизовано користувача")
    is_active: bool = Field(default=True, description="Чи активний обліковий запис")
    access_level: AccessLevel = Field(default=AccessLevel.GUEST, description="Рівень доступу")

    # Гранулярні дозволи
    can_manage_sessions: bool = Field(default=False, description="Керування сесіями Telethon")
    can_manage_chats: bool = Field(default=False, description="Керування списком чатів")
    can_manage_users: bool = Field(default=False, description="Зміна прав користувачів")

    created_at: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    @property
    def display_name(self) -> str:
        """Повертає пріоритетне ім'я для відображення (ПІБ, позивний або Telegram-ім'я)."""
        if self.call_sign:
            return f"[{self.call_sign}] {self.surname or ''} {self.official_name or self.first_name or ''}".strip()
        if self.surname and self.official_name:
            return f"{self.surname} {self.official_name}"
        if self.first_name:
            return f"{self.first_name} {self.last_name or ''}".strip()
        if self.username:
            return f"@{self.username}"
        return f"ID: {self.id}"

