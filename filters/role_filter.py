# filters/role_filter.py
from typing import Optional
from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from database.models.user import AccessLevel, UserModel


class RoleFilter(BaseFilter):
    """
    Фільтр для перевірки мінімального рівня доступу користувача.
    
    Використання в роутерах:
    `@router.message(RoleFilter(AccessLevel.ADMIN))`
    `@router.callback_query(RoleFilter(AccessLevel.USER))`
    """

    def __init__(self, min_level: int = AccessLevel.USER):
        self.min_level = min_level

    async def __call__(
        self,
        event: TelegramObject,
        user: Optional[UserModel] = None,
    ) -> bool:
        if not user or not user.is_active:
            return False
        return user.access_level >= self.min_level

