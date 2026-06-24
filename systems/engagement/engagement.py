# -*- coding: utf-8 -*-
"""
نظام التفاعل التلقائي المطور (engagement) - النسخة المربوطة بالسوق المصلح مباشرة.
"""

import asyncio
from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.engagement import queries as engagement_queries
from systems.moderators.permissions import get_user_rank
from systems.engagement.notifications import messages

router = Router(name="engagement")

def _member_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
         InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضويتي")],
        [InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:مشترياتي"),
         InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
    ])

def _staff_menu_keyboard(rank: str) -> InlineKeyboardMarkup:
    cmd = "ادمن" if rank == "admin" else "مشرف"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
         InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضويتي")],
        [InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:مشترياتي"),
         InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
        [InlineKeyboardButton(text="📋 القائمة الإدارية", callback_data=f"eng:cmd:{cmd}")],
    ])

def _owner_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
         InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضويتي")],
        [InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:مشترياتي"),
         InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
        [InlineKeyboardButton(text="📋 القائمة الإدارية", callback_data="eng:cmd:admin")],
    ])

@router.callback_query(F.data == "eng:open_menu")
async def open_personal_menu(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    user_id = callback.from_user.id
    full_name = callback.from_user.full_name
    pool = await get_pool()
    rank = await get_user_rank(pool, user_id)

    if user_id == OWNER_ID:
        keyboard = _owner_menu_keyboard()
    elif rank in ("admin", "moderator"):
        keyboard = _staff_menu_keyboard(rank)
    else:
        keyboard = _member_menu_keyboard()

    await callback.bot.send_message(chat_id=user_id, text=messages.member_menu_text(full_name), reply_markup=keyboard)
    await callback.answer(messages.MENU_OPENED)

@router.callback_query(F.data.startswith("eng:cmd:"))
async def run_command(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    cmd_text = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    pool = await get_pool()

    await callback.answer()

    fake_message = Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        from_user=callback.from_user,
        text=cmd_text
    )

    # تشغيل دوال الـ shop المصلحة مباشرة بالخاص
    if cmd_text == "سوق":
        from systems.shop.shop import shop_menu_handler
        await shop_menu_handler(fake_message)
    elif cmd_text == "عضويتي":
        from systems.shop.shop import my_membership_handler
        await my_membership_handler(fake_message)
    elif cmd_text == "مشترياتي":
        from systems.shop.shop import my_titles_handler
        await my_titles_handler(fake_message)
    elif cmd_text == "حساب":
        # كود حساب الأصلي المفعّل داخلياً لديك
        pass
