"""
keyboards/ - Динамічні конструктори клавіатур Refridex OS.
"""
from .reply_keyboard import get_main_reply_keyboard, MenuItem, MENU_ITEMS
from .inline_keyboard import (
    get_block_navigation_keyboard,
    get_block_action_keyboard,
    get_profile_inline_keyboard,
)

__all__ = [
    "get_main_reply_keyboard",
    "MenuItem",
    "MENU_ITEMS",
    "get_block_navigation_keyboard",
    "get_block_action_keyboard",
    "get_profile_inline_keyboard",
]
