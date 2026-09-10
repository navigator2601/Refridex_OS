# handlers/__init__.py
"""
handlers/ - Роутери обробки подій Telegram (Aiogram v3).
"""
from aiogram import Router

from handlers.common import router as common_router
from handlers.guest import router as guest_router
from handlers.admin import router as admin_router
from handlers.montage import router as montage_router

# Головний роутер проекту, який об'єднує всі підпорядковані роутери
main_router = Router(name="main_router")
main_router.include_router(common_router)
main_router.include_router(guest_router)
main_router.include_router(admin_router)
main_router.include_router(montage_router)

__all__ = ["main_router", "common_router", "guest_router", "admin_router", "montage_router"]
