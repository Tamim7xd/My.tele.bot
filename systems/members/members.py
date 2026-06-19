"""
نظام الأعضاء - الملف الرئيسي.

يحتوي على:
- تسجيل كل عضو يكتب رسالة في المجموعة تلقائياً
- زيادة عداد رسائله
- حفظ آيدي المجموعة في الإعدادات (يُستخدم من المجدولات مثل moderation)
- أمر "حساب" ومرادفاته لعرض بطاقة الحساب
  - عضو عادي: يشوف حسابه فقط
  - أدمن/مشرف: بالرد على عضو آخر، يشوف حسابه

⚠️ ملاحظة مهمة عن الترتيب:
aiogram يجرب الـ handlers بترتيب تسجيلها، ويتوقف عند أول واحد يطابق.
لذلك show_account (الذي له شرط نص محدد) مسجل قبل register_and_count
(الذي يطابق كل الرسائل بدون شرط نص) - وإلا لن تصل أي رسالة لـ show_account.

هذا الملف مستقل تماماً - حذفه أو تعديله لا يؤثر على أي نظام آخر،
بشرط ألا تستورده أنظمة أخرى مباشرة (الأفضل التواصل عبر queries.py المشترك).
"""

import asyncio

from aiogram import Router, F
from aiogram.types import Message

from core.database import get_pool, get_setting, set_setting
from systems.members import queries
from systems.members.notifications import messages
from systems.moderators import permissions
from systems.levels import levels as levels_system
from core.config import DEFAULT_DELETE_DELAY


router = Router(name="members")


GROUP_ID_KEY = "group_id"


ACCOUNT_COMMANDS = {"حساب", "حسابي", "الحساب", "معلوماتي", "معلومات"}


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
            if await permissions.is_staff(pool, message.from_user.id):
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

    games_played = member["games_played"]
    games_won = member["games_won"]

    active_title_name = None
    membership_name = None

    try:
        from systems.shop import queries as shop_queries
        from systems.shop import member_queries as shop_member_queries

        active_title_id = await shop_member_queries.get_active_title(pool, target_user.id)
        if active_title_id:
            title = await shop_queries.get_title_by_id(pool, active_title_id)
            if title:
                active_title_name = title["name"]

        membership_status = await shop_member_queries.get_member_membership_status(pool, target_user.id)
        if membership_status:
            membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
            if membership:
                membership_name = membership["name"]
    except Exception:
        pass

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
        active_title_name=active_title_name,
        membership_name=membership_name,
    )

    sent = await message.reply(text)

    # لا نحذف بطاقة الحساب تلقائياً إذا الأدمن يستعرض حساب عضو آخر
    if not is_viewing_other:
        await _auto_delete(message, sent)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def register_and_count(message: Message) -> None:
    """
    يعمل مع كل رسالة في المجموعة (ما عدا أوامر الحساب التي عولجت أعلاه):
    - يسجل العضو إذا لم يكن مسجلاً
    - يزيد عداد رسائله
    - يحفظ آيدي المجموعة في الإعدادات (أول مرة فقط)
    - يستدعي نظام المستويات لفحص رفع المستوى
    """
    if message.from_user is None:
        return

    pool = await get_pool()

    # حفظ آيدي المجموعة (يُستخدم من المجدولات - مرة واحدة فقط)
    saved_group_id = await get_setting(pool, GROUP_ID_KEY)
    if saved_group_id != message.chat.id:
        await set_setting(pool, GROUP_ID_KEY, message.chat.id)

    await queries.ensure_member_exists(
        pool,
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    new_count = await queries.increment_message_count(pool, message.from_user.id)

    # فحص رفع المستوى بعد زيادة عداد الرسائل
    await levels_system.check_level_up(
        pool=pool,
        bot=message.bot,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        messages_count=new_count,
    )


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
