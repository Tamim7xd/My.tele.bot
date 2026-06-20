"""
نظام الرصيد - أمر الترتيب (Leaderboard).

يحتوي على أمر "الأغنى" / "ترتيب" / "الترتيب" لعرض أعلى 3 أعضاء رصيداً.

هذا الملف مستقل - حذفه أو تعديله لا يؤثر على wallet.py
أو أي نظام آخر يستخدم دوال wallet.py.
"""

import asyncio

from aiogram import Router, F
from aiogram.types import Message

from core.database import get_pool
from systems.wallet import wallet
from systems.wallet.notifications import messages
from core.config import DEFAULT_DELETE_DELAY


router = Router(name="wallet_leaderboard")


LEADERBOARD_COMMANDS = {"الأغنى", "ترتيب", "الترتيب", "ترتيب الرصيد"}


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(LEADERBOARD_COMMANDS),
)
async def show_leaderboard(message: Message) -> None:
    """يعرض قائمة أعلى 3 أعضاء رصيداً."""
    pool = await get_pool()

    top_members = await wallet.get_top_balances(pool, limit=3)

    entries = [
        (i + 1, row["username"], row["full_name"], row["balance"])
        for i, row in enumerate(top_members)
    ]

    text = messages.leaderboard_text(entries)

    sent = await message.reply(text)

    await asyncio.sleep(DEFAULT_DELETE_DELAY)

    try:
        await message.delete()
    except Exception:
        pass

    try:
        await sent.delete()
    except Exception:
        pass
