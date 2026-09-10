# database/models/user.py
from datetime import datetime
from enum import Enum, IntEnum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AccessLevel(IntEnum):
    """
    Ієрархія рівнів доступу системи Refridex OS:
    0   - 🔒 Гість [Level 0]
    1   - 🧭 Техно-Навігатор [L1]
    3   - 🔧 Системний Інженер [L3]
    6   - 📊 Керівник Протоколів [L6]
    10  - 🛡️ Адміністратор Ядра [L10]
    100 - 🧬 Архітектор Системи [ROOT]
    101 - 🌀 Пробуджений Refridex [L∞]
    """
    GUEST = 0               # 🔒 Гість [Level 0]
    TECHNO_NAVIGATOR = 1    # 🧭 Техно-Навігатор [L1] - звичайний користувач
    SYSTEM_ENGINEER = 3     # 🔧 Системний Інженер [L3] - монтажники і старші
    PROTOCOL_LEAD = 6       # 📊 Керівник Протоколів [L6] - старші монтажники / диспетчери
    CORE_ADMIN = 10         # 🛡️ Адміністратор Ядра [L10] - керування користувачами та правами
    SYSTEM_ARCHITECT = 100  # 🧬 Архітектор Системи [ROOT] - адміністратор повного доступу
    AWAKENED = 101          # 🌀 Пробуджений Refridex [L∞] - суперадмін системи

    # Сумісні аліаси для зворотної сумісності коду
    USER = 1
    MODERATOR = 6
    ADMIN = 10

    @property
    def title(self) -> str:
        titles = {
            self.GUEST: "Гість",
            self.TECHNO_NAVIGATOR: "Техно-Навігатор",
            self.SYSTEM_ENGINEER: "Системний Інженер",
            self.PROTOCOL_LEAD: "Керівник Протоколів",
            self.CORE_ADMIN: "Адміністратор Ядра",
            self.SYSTEM_ARCHITECT: "Архітектор Системи",
            self.AWAKENED: "Пробуджений Refridex",
        }
        return titles.get(self, f"Рівень {self.value}")

    @property
    def badge(self) -> str:
        badges = {
            self.GUEST: "🔒 Гість [Level 0]",
            self.TECHNO_NAVIGATOR: "🧭 Техно-Навігатор [L1]",
            self.SYSTEM_ENGINEER: "🔧 Системний Інженер [L3]",
            self.PROTOCOL_LEAD: "📊 Керівник Протоколів [L6]",
            self.CORE_ADMIN: "🛡️ Адміністратор Ядра [L10]",
            self.SYSTEM_ARCHITECT: "🧬 Архітектор Системи [ROOT]",
            self.AWAKENED: "🌀 Пробуджений Refridex [L∞]",
        }
        return badges.get(self, f"Рівень {self.value}")

    def is_admin(self) -> bool:
        return self >= self.CORE_ADMIN

    def is_architect(self) -> bool:
        return self >= self.SYSTEM_ARCHITECT

    def is_lead(self) -> bool:
        return self >= self.PROTOCOL_LEAD

    def is_engineer(self) -> bool:
        return self >= self.SYSTEM_ENGINEER

    def is_navigator(self) -> bool:
        return self >= self.TECHNO_NAVIGATOR


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
        """Повертає пріоритетне ім'я для відображення (позивний, ПІБ, ім'я або юзернейм)."""
        if self.call_sign:
            return f"[{self.call_sign}] {self.surname or ''} {self.official_name or self.first_name or ''}".strip()
        if self.surname and self.official_name:
            return f"{self.surname} {self.official_name}"
        if self.official_name:
            return self.official_name
        if self.first_name:
            return f"{self.first_name} {self.last_name or ''}".strip()
        if self.username:
            return f"@{self.username}"
        return f"ID: {self.id}"
