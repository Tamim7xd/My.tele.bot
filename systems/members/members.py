"""
نظام الأعضاء - الملف الرئيسي.

يحتوي على:
- تسجيل كل عضو يكتب رسالة في المجموعة تلقائياً
- زيادة عداد رسائله
- أمر "حساب" ومرادفاته لعرض بطاقة الحساب
  - عضو عادي: يشوف حسابه فقط
  - أدمن/مشرف: بالرد على عضو آخر، يشوف حسابه

هذا الملف مستقل تماماً - حذفه أو تعديله لا يؤثر على أي نظام آخر،
بشرط ألا تستورده أنظمة أخرى مباشرة (الأفضل التواصل عبر queries.py المشترك).
"""

import asyncio

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from core.database import get_pool
from systems.members import queries
from systems.members.notifications import messages
from core.config import DEFAULT_DELETE_DELAY


router = Router(name="members")


# ===== الكلمات التي تشغّل أمر الحساب =====
ACCOUNT_COMMANDS = {"حساب", "حسابي", "الحساب", "معلوماتي", "معلومات"}


@router.message("""
نظام الأعضاء - الملف الرئيسي.

يحتوي على:
- تسجيل كل عضو يكتب رسالة في المجموعة تلقائياً
- زيادة عداد رسائله
- أمر "حساب" ومرادفاته لعرض بطاقة الحساب
  - عضو عادي: يشوف حسابه فقط
  - أدمن/مشرف: بالرد على عضو آخر، يشوف حسابه

هذا الملف مستقل تماماً - حذفه أو تعديله لا يؤثر على أي نظام آخر،
بشرط ألا تستورده أنظمة أخرى مباشرة (الأفضل التواصل عبر queries.py المشترك).
"""

import asyncio

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from core.database import get_pool
from systems.members import queries
from systems.members.notifications import messages
from core.config import DEFAULT_DELETE_DELAY


router = Router(name="members")


# ===== الكلمات التي تشغّل أمر الحساب =====
ACCOUNT_COMMANDS = {"حساب", "حسابي", "الحساب", "معلوماتي", "معلومات"}


@router.message(F.chat.type.in_({"group", "supergroup"})
async def register_and_count(message: Message) -> None:
    """
    يعمل مع كل رسالة في المجموعة:
    - يسجل العضو إذا لم يكن مسجلاً
    - يزيد عداد رسائله

    ملاحظة: هذا الهاندلر لا يستخدم F.text فقط حتى يسجل حتى
    لو كانت الرسالة صورة/ملصق/إلخ. لكنه لا يعالج النص هنا.
    """
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


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(ACCOUNT_COMMANDS),
)
async def show_account(message: Message) -> None:
    """
    يعرض بطاقة الحساب عند كتابة "حساب" أو أحد مرادفاته.

    - إذا الرسالة رد على عضو آخر، وكاتب الأمر أدمن/مشرف => يعرض حساب العضو المردود عليه
    - إذا الرسالة رد على عضو آخر، وكاتب الأمر عضو عادي => رسالة "لا صلاحية"
    - إذا لا يوجد رد => يعرض حساب كاتب الأمر نفسه
    """
    if message.from_user is None:
        return

    pool = await get_pool()

    target_user = message.from_user
    is_viewing_other = False

    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user

        if replied_user.id != message.from_user.id:
            caller_rank = await queries.get_rank(pool, message.from_user.id)

            if caller_rank in ("moderator", "admin", "owner"):
                target_user = replied_user
                is_viewing_other = True
            else:
                warning = await message.reply(messages.NO_PERMISSION_VIEW_OTHERS)
                await _auto_delete(message, warning)
                return

    # تسجيل العضو الهدف إن لم يكن مسجلاً (احتياطي)
    await queries.ensure_member_exists(
        pool,
        user_id=target_user.id,
        username=target_user.username,
        full_name=target_user.full_name,
    )

    member = await queries.get_member(pool, target_user.id)
    warnings_count = await queries.get_warnings_count(pool, target_user.id)
    violations_count = await queries.get_violations_count(pool, target_user.id)

    # games_played / games_won سيتم ربطها مستقبلاً مع نظام الألعاب
    # حالياً نعرض 0 كقيمة افتراضية حتى نبني نظام الألعاب
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

    # لا نحذف بطاقة الحساب تلقائياً إذا الأدمن يستعرض حساب عضو آخر
    # (يحتاج وقت للقراءة)، لكن نحذف رسالة الأمر نفسها فقط في الحالة العادية
    if not is_viewing_other:
        await _auto_delete(message, sent)


async def _auto_delete(command_message: Message, response_message: Message) -> None:
    """
    يحذف رسالة الأمر ورد البوت بعد المدة المحددة (DEFAULT_DELETE_DELAY).
    يتجاهل الأخطاء (مثلاً لو الرسالة محذوفة بالفعل أو البوت بدون صلاحية حذف).
    """
    await asyncio.sleep(DEFAULT_DELETE_DELAY)

    try:
        await command_message.delete()
    except Exception:
        pass

    try:
        await response_message.delete()
    except Exception:
        pass

async def register_and_count(message: Message) -> None:
    """
    يعمل مع كل رسالة في المجموعة:
    - يسجل العضو إذا لم يكن مسجلاً
    - يزيد عداد رسائله

    ملاحظة: هذا الهاندلر لا يستخدم F.text فقط حتى يسجل حتى
    لو كانت الرسالة صورة/ملصق/إلخ. لكنه لا يعالج النص هنا.
    """
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


@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    F.text.in_(ACCOUNT_COMMANDS),
)
async def show_account(message: Message) -> None:
    """
    يعرض بطاقة الحساب عند كتابة "حساب" أو أحد مرادفاته.

    - إذا الرسالة رد على عضو آخر، وكاتب الأمر أدمن/مشرف => يعرض حساب العضو المردود عليه
    - إذا الرسالة رد على عضو آخر، وكاتب الأمر عضو عادي => رسالة "لا صلاحية"
    - إذا لا يوجد رد => يعرض حساب كاتب الأمر نفسه
    """
    if message.from_user is None:
        return

    pool = await get_pool()

    target_user = message.from_user
    is_viewing_other = False

    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user

        if replied_user.id != message.from_user.id:
            caller_rank = await queries.get_rank(pool, message.from_user.id)

            if caller_rank in ("moderator", "admin", "owner"):
                target_user = replied_user
                is_viewing_other = True
            else:
                warning = await message.reply(messages.NO_PERMISSION_VIEW_OTHERS)
                await _auto_delete(message, warning)
                return

    # تسجيل العضو الهدف إن لم يكن مسجلاً (احتياطي)
    await queries.ensure_member_exists(
        pool,
        user_id=target_user.id,
        username=target_user.username,
        full_name=target_user.full_name,
    )

    member = await queries.get_member(pool, target_user.id)
    warnings_count = await queries.get_warnings_count(pool, target_user.id)
    violations_count = await queries.get_violations_count(pool, target_user.id)

    # games_played / games_won سيتم ربطها مستقبلاً مع نظام الألعاب
    # حالياً نعرض 0 كقيمة افتراضية حتى نبني نظام الألعاب
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

    # لا نحذف بطاقة الحساب تلقائياً إذا الأدمن يستعرض حساب عضو آخر
    # (يحتاج وقت للقراءة)، لكن نحذف رسالة الأمر نفسها فقط في الحالة العادية
    if not is_viewing_other:
        await _auto_delete(message, sent)


async def _auto_delete(command_message: Message, response_message: Message) -> None:
    """
    يحذف رسالة الأمر ورد البوت بعد المدة المحددة (DEFAULT_DELETE_DELAY).
    يتجاهل الأخطاء (مثلاً لو الرسالة محذوفة بالفعل أو البوت بدون صلاحية حذف).
    """
    await asyncio.sleep(DEFAULT_DELETE_DELAY)

    try:
        await command_message.delete()
    except Exception:
        pass

    try:
        await response_message.delete()
    except Exception:
        pass
