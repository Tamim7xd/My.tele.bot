"""
نظام الحماية - منع انضمام البوتات تلقائياً.

عند انضمام أي عضو جديد (new_chat_members)، إن كان بوتاً (is_bot=True)
وليس البوت نفسه، يُطرَد تلقائياً إن كانت ميزة "block_bots" مفعّلة
من اللوحة (مفعّلة افتراضياً).
"""

from aiogram import Router, F
from aiogram.types import Message

from core.database import get_pool
from systems.protection import queries as protection_queries


router = Router(name="protection_bot_guard")


@router.message(F.chat.type.in_({"group", "supergroup"}), F.new_chat_members)
async def block_new_bots(message: Message) -> None:
    if not message.new_chat_members:
        return

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)

    if not settings.get("block_bots", True):
        return

    bot_info = await message.bot.me()

    for new_member in message.new_chat_members:
        if not new_member.is_bot:
            continue

        if new_member.id == bot_info.id:
            continue  # لا نطرد أنفسنا

        try:
            await message.chat.ban(new_member.id)
            await message.chat.unban(new_member.id)  # طرد بدون حظر دائم
        except Exception:
            pass

        try:
            await message.answer(f"🤖 تم طرد البوت {new_member.full_name} تلقائياً.")
        except Exception:
            pass
