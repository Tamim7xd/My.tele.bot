"""
نظام الإداريين - الملف الرئيسي.

يحتوي على:
- أمر "ترقية" بالرد على عضو (member -> moderator -> admin) - المالك فقط
- أمر "تخفيض" بالرد على عضو (admin -> moderator -> member) - المالك فقط
- فلتر عام: أي رسالة تبدأ بـ "/" في المجموعة تُحذف فوراً بدون أي رد

هذا الملف مستقل - حذفه أو تعديله لا يؤثر على أي نظام آخر،
لكن أنظمة أخرى (rewards, moderation, archive) تستخدم
systems/moderators/permissions.py للتحقق من الصلاحيات.
"""

from aiogram import Router, F
from aiogram.types import Message

from core.database import get_pool
from core.config import OWNER_ID
from systems.members import queries as members_queries
from systems.moderators import queries
from systems.moderators.notifications import messages


router = Router(name="moderators")


PROMOTE_COMMANDS = {"ترقية"}
DEMOTE_COMMANDS = {"تخفيض"}


# ===== فلتر عام: حذف أي رسالة تبدأ بـ "/" في المجموعة =====
@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.startswith("/"),
)
async def delete_slash_commands(message: Message) -> None:
    """
    أي رسالة تبدأ بـ "/" في المجموعة تُحذف فوراً.
    البوت لا يتفاعل معها أو يرد عليها أبداً، بغض النظر عن كاتبها.
    """
    try:
        await message.delete()
    except Exception:
        pass


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(PROMOTE_COMMANDS),
)
async def promote_member(message: Message) -> None:
    """
    يرقي العضو المردود عليه لرتبة أعلى (member -> moderator -> admin).
    المالك فقط يمكنه استخدام هذا الأمر.
    """
    if message.from_user is None:
        return

    if message.from_user.id != OWNER_ID:
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return

    target = message.reply_to_message.from_user
    pool = await get_pool()

    await members_queries.ensure_member_exists(
        pool,
        user_id=target.id,
        username=target.username,
        full_name=target.full_name,
    )

    new_rank = await queries.promote(pool, target.id)

    if new_rank is None:
        await message.reply(messages.ALREADY_TOP_RANK)
        return

    text = messages.promotion_notification(
        full_name=target.full_name,
        username=target.username,
        new_rank=new_rank,
        by_full_name=message.from_user.full_name,
    )

    await message.answer(text)


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(DEMOTE_COMMANDS),
)
async def demote_member(message: Message) -> None:
    """
    يخفض العضو المردود عليه لرتبة أدنى (admin -> moderator -> member).
    المالك فقط يمكنه استخدام هذا الأمر.
    """
    if message.from_user is None:
        return

    if message.from_user.id != OWNER_ID:
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return

    target = message.reply_to_message.from_user
    pool = await get_pool()

    await members_queries.ensure_member_exists(
        pool,
        user_id=target.id,
        username=target.username,
        full_name=target.full_name,
    )

    new_rank = await queries.demote(pool, target.id)

    if new_rank is None:
        await message.reply(messages.ALREADY_MEMBER)
        return

    text = messages.demotion_notification(
        full_name=target.full_name,
        username=target.username,
        new_rank=new_rank,
        by_full_name=message.from_user.full_name,
    )

    await message.answer(text)
