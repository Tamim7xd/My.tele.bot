"""
نظام المتجر (shop) - حماية "no_replies".

أي عضوية فيها "no_replies": true (مثل Super VIP) تمنع الأعضاء العاديين
من الرد (reply) على رسائل مالكها. الإداريون (مشرف/أدمن/المالك) مستثنون.
"""

from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message

from core.database import get_pool
from systems.moderators import permissions
from systems.shop import queries as shop_queries
from systems.shop import member_queries as shop_member_queries


router = Router(name="shop_no_replies")


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def block_replies_to_protected_members(message: Message) -> None:
    if message.from_user is None or message.reply_to_message is None:
        raise SkipHandler

    replied_user = message.reply_to_message.from_user

    if replied_user is None or replied_user.id == message.from_user.id:
        raise SkipHandler

    pool = await get_pool()

    if await permissions.is_staff(pool, message.from_user.id):
        raise SkipHandler

    status = await shop_member_queries.get_member_membership_status(pool, replied_user.id)

    if status is None:
        raise SkipHandler

    membership = await shop_queries.get_membership_by_id(pool, status["membership_id"])

    if membership is None or not membership.get("no_replies"):
        raise SkipHandler

    try:
        await message.delete()
    except Exception:
        pass

    # توقف هنا عمداً - لا SkipHandler، الرسالة حُذفت
