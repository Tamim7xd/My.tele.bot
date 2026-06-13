"""
نظام الأعضاء - الملف الرئيسي.

ملاحظة مهمة عن الترتيب:
aiogram يجرب الـ handlers بترتيب تسجيلها، ويتوقف عند أول واحد يطابق.
لذلك show_account (الذي له شرط نص محدد) مسجل قبل register_and_count
(الذي يطابق كل الرسائل بدون شرط نص) - وإلا لن تصل أي رسالة لـ show_account.
"""

import asyncio

from aiogram import Router, F
from aiogram.types import Message

from core.database import get_pool
from systems.members import queries
from systems.members.notifications import messages
from systems.moderators import permissions
from core.config import DEFAULT_DELETE_DELAY


router = Router(name="members")


ACCOUNT_COMMANDS = {"حساب", "حسابي", "الحساب", "معلوماتي", "معلومات"}


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(ACCOUNT_COMMANDS),
)
async def show_account(message: Message) -> None:
    if message.from_user is None:
        return

    pool = await get_pool()

    target_user = message.from_user
    is_viewing_other = False

    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user

        if replied_user.id != message.from_user.id:
            if await permissions.is_staff(pool, message.from_user.id):
                target_user = replied_user
                is_viewing_other = True
            else:
                warning = await message.reply(messages.NO_PERMISSION_VIEW_OTHERS)
                await _auto_delete(message, warning)
                return

    await queries.ensure_member_exists(
        pool,
        user_id=target_user.id,
        username=target_user.username,
        full_name=target_user.full_name,
    )

    member = await queries.get_member(pool, target_user.id)
    warnings_count = await queries.get_warnings_count(pool, target_user.id)
    violations_count = await queries.get_violations_count(pool, target_user.id)

    games_played = 0
    games_won = 0

    text = messages.account_card_text(
        full_name=member["full_name"],
        username=member["username"],
        level=member["level"],
        messages_count=member["messages_count"],
        balance=member["balance"],
        warnings_count=warnings_count,
        violations_count=violations_count,
        games_played=games_played,
        games_won=games_won,
    )

    sent = await message.reply(text)

    if not is_viewing_other:
        await _auto_delete(message, sent)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def register_and_count(message: Message) -> None:
    if message.from_user is None:
        return

    pool = await get_pool()

    await queries.ensure_member_exists(
        pool,
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    await queries.increment_message_count(pool, message.from_user.id)


async def _auto_delete(command_message: Message, response_message: Message) -> None:
    await asyncio.sleep(DEFAULT_DELETE_DELAY)

    try:
        await command_message.delete()
    except Exception:
        pass

    try:
        await response_message.delete()
    except Exception:
        pass
