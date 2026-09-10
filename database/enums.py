# database/enums.py
from enum import IntEnum, Enum


class AccessLevel(IntEnum):
    """Рівні доступу користувачів у системі Refridex OS."""
    GUEST = 0      # Гість (без доступу до функціоналу)
    USER = 1       # Звичайний користувач / монтажник
    MODERATOR = 2  # Модератор / бригадир
    ADMIN = 3      # Адміністратор системи

    @property
    def title(self) -> str:
        names = {
            self.GUEST: "Гість",
            self.USER: "Користувач",
            self.MODERATOR: "Модератор",
            self.ADMIN: "Адміністратор",
        }
        return names.get(self, "Невідомо")

    @classmethod
    def is_admin(cls, level: int) -> bool:
        return level >= cls.ADMIN

    @classmethod
    def is_user(cls, level: int) -> bool:
        return level >= cls.USER


class AuthStatus(str, Enum):
    """Статуси спроби авторизації."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

