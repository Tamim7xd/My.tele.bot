"""
نظام التنظيف - الملف الرئيسي.

أمر "#تنظيف" (للمالك والأدمن فقط):
1. يعرض عد تنازلي متحرك (5 -> 0) بتعديل رسالة واحدة
2. يعرض "جارِ التنظيف..."
3. يحذف نطاقاً من آخر الرسائل (بالاعتماد على message_id الحالي
   والرجوع للخلف CLEANUP_RANGE رسالة)، متجاهلاً أي رسالة
   فشل حذفها (مثلاً أقدم من 48 ساعة - قيد تيليجرام)
4. يحذف رسالة "#تنظيف" نفسها ضمن النطاق
5. يعرض رسالة "تم حذف X رسالة" تختفي بعد 5 ثوانٍ

ملاحظة عن الحدود:
تيليجرام لا يسمح بحذف رسائل أقدم من 48 ساعة، ولا يوجد API
لجلب كل تاريخ المحادثة. لذلك نعتمد على نطاق رقمي حول message_id
الحالي (CLEANUP_RANGE)، وهو قابل للتعديل من لوحة التحكم لاحقاً.

هذا الملف مستقل تماماً عن باقي الأنظمة.
"""

import asyncio

from aiogram import Router, F
from aiogram.types import Message

from core.database import get_pool, get_setting
from systems.moderators import permissions
from systems.cleanup.notifications import messages
from core.config import DEFAULT_DELETE_DELAY


router = Router(name="cleanup")


CLEANUP_COMMAND = "#تنظيف"

CLEANUP_RANGE_KEY = "cleanup_range"

# القيمة الافتراضية (تُستخدم فقط أول مرة قبل أي تعديل من لوحة التحكم)
DEFAULT_CLEANUP_RANGE = 100


async def get_cleanup_range(pool) -> int:
    """يرجع عدد رسائل التنظيف الحالي من قاعدة البيانات (أو الافتراضي)."""
    return await get_setting(pool, CLEANUP_RANGE_KEY, DEFAULT_CLEANUP_RANGE)


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text == CLEANUP_COMMAND,
)
async def cleanup_messages(message: Message) -> None:
    if message.from_user is None:
        return

    pool = await get_pool()

    # فقط المالك والأدمن (deduct/reward owner-level) - نستخدم is_staff
    # ثم نستثني المشرف العادي بالتحقق من الرتبة مباشرة عبر has_permission "all"/admin
    if not await _is_owner_or_admin(pool, message.from_user.id):
        warning = await message.reply(messages.NO_PERMISSION)
        await asyncio.sleep(DEFAULT_DELETE_DELAY)
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await warning.delete()
        except Exception:
            pass
        return

    chat_id = message.chat.id
    command_message_id = message.message_id

    # ===== عرض العد التنازلي =====
    status_message = await message.answer(messages.countdown_text(5))

    for seconds_left in (4, 3, 2, 1, 0):
        await asyncio.sleep(1)
        try:
            await status_message.edit_text(messages.countdown_text(seconds_left))
        except Exception:
            pass

    try:
        await status_message.edit_text(messages.CLEANING_NOW)
    except Exception:
        pass

    # ===== حذف نطاق من الرسائل =====
    deleted_count = 0

    cleanup_range = await get_cleanup_range(pool)

    start_id = command_message_id
    end_id = max(1, command_message_id - cleanup_range)

    for msg_id in range(start_id, end_id - 1, -1):
        try:
            await message.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            deleted_count += 1
        except Exception:
            continue

    # ===== الرسالة النهائية =====
    try:
        await status_message.edit_text(messages.done_text(deleted_count))
    except Exception:
        status_message = await message.answer(messages.done_text(deleted_count))

    await asyncio.sleep(DEFAULT_DELETE_DELAY)
    try:
        await status_message.delete()
    except Exception:
        pass


async def _is_owner_or_admin(pool, user_id: int) -> bool:
    """يتحقق إن كان العضو owner أو admin (وليس مشرف عادي)."""
    from core.config import OWNER_ID

    if user_id == OWNER_ID:
        return True

    async with pool.acquire() as conn:
        rank = await conn.fetchval(
            "SELECT rank FROM members WHERE user_id = $1", user_id
        )

    return rank in ("admin", "owner")
