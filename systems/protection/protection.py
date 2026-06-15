"""
نظام الحماية (protection) - محرك الفلترة الرئيسي.

يفحص كل رسالة في المجموعة:
1. إذا كانت من المالك/الأدمن/المشرف -> تُعفى تماماً
2. يحدد نوع المحتوى (رابط/ملف/فيديو/صوت/موقع/صورة/ملصق/GIF/نص)
3. يتحقق من إعدادات الحماية العامة + استثناءات العضو الفردية
4. إذا كانت مخالفة:
   - يحذف الرسالة
   - يرد على العضو "🚫 لا تتجاوز القوانين" (يُحذف بعد 5 ثوانٍ)
   - يسجل في protection_log

⚠️ ملاحظة عن الترتيب وآلية التمرير:
هذا الـ router يفحص كل الرسائل بدون شرط نص محدد (لاكتشاف الروابط/الملفات/...).
بما أن فلتره يطابق كل رسائل المجموعة، فإن عدم إيجاد مخالفة يجب أن "يُمرر"
المعالجة للأنظمة التالية (announcements, members) - يتم ذلك برفع
SkipHandler، وإلا فستتوقف كل الرسائل السليمة عند هذا الـ router فقط.

عند وجود مخالفة فعلية، تُحذف الرسالة ولا تُرفع SkipHandler (تنتهي
المعالجة هنا عمداً، فلا يسجلها members_system كرسالة عادية).

يجب أن يُسجَّل بعد الأنظمة ذات الأوامر المحددة (rewards, moderation, staff,
cleanup) وقبل announcements و members.
"""

import asyncio
import re

from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message

from core.database import get_pool
from core.config import DEFAULT_DELETE_DELAY
from systems.moderators import permissions
from systems.protection import queries as protection_queries
from systems.protection.text_normalizer import find_matched_word
from systems.protection.notifications import messages


router = Router(name="protection")


_URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|@\w{4,})",
    re.IGNORECASE,
)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_message(message: Message) -> None:
    if message.from_user is None:
        raise SkipHandler

    pool = await get_pool()
    user_id = message.from_user.id

    # ===== استثناء المالك/الأدمن/المشرف =====
    if await permissions.is_staff(pool, user_id):
        raise SkipHandler

    settings = await protection_queries.get_protection_settings(pool)

    violation_type, content_preview = await _detect_violation(message, settings, pool, user_id)

    if violation_type is None:
        # لا توجد مخالفة - نُكمل المعالجة لباقي الأنظمة (announcements, members)
        raise SkipHandler

    # ===== تنفيذ الحذف =====
    try:
        await message.delete()
    except Exception:
        raise SkipHandler

    await protection_queries.log_deleted_message(pool, user_id, violation_type, content_preview)

    try:
        warning = await message.answer(messages.VIOLATION_REPLY)
        asyncio.create_task(_delete_later(warning, DEFAULT_DELETE_DELAY))
    except Exception:
        pass

    # الرسالة حُذفت - نوقف المعالجة هنا فعلاً (لا SkipHandler)


async def _detect_violation(message: Message, settings: dict, pool, user_id: int) -> tuple[str | None, str | None]:
    """
    يفحص الرسالة ويحدد نوع المخالفة (إن وُجدت) ومعاينة المحتوى.
    يرجع (violation_type, content_preview) أو (None, None) إن لم تكن مخالفة.
    """

    # ===== الموقع =====
    if message.location is not None:
        if await _is_violation(pool, user_id, settings, "location"):
            return "location", f"خط العرض: {message.location.latitude}, خط الطول: {message.location.longitude}"

    # ===== الفيديو =====
    if message.video is not None:
        if await _is_violation(pool, user_id, settings, "videos"):
            return "videos", message.caption or "(فيديو بدون وصف)"

    # ===== البصمات الصوتية (voice notes) =====
    if message.voice is not None:
        if await _is_violation(pool, user_id, settings, "voice"):
            return "voice", "(بصمة صوتية)"

    # ===== الملفات/المستندات =====
    if message.document is not None:
        if await _is_violation(pool, user_id, settings, "files"):
            file_name = message.document.file_name or "(ملف بدون اسم)"
            return "files", file_name

    # ===== الصور =====
    if message.photo is not None:
        if await _is_violation(pool, user_id, settings, "photos"):
            return "photos", message.caption or "(صورة بدون وصف)"

    # ===== الملصقات/GIF =====
    if message.sticker is not None or message.animation is not None:
        if await _is_violation(pool, user_id, settings, "stickers_gifs"):
            kind = "ملصق" if message.sticker is not None else "GIF"
            return "stickers_gifs", f"({kind})"

    # ===== النص: روابط + كلام مسيء =====
    text = message.text or message.caption

    if text:
        # الروابط
        if await _is_violation(pool, user_id, settings, "links"):
            if _URL_PATTERN.search(text):
                return "links", text

        # الكلام المسيء
        if await _is_violation(pool, user_id, settings, "bad_words"):
            banned_words = settings.get("banned_words", [])
            matched = find_matched_word(text, banned_words)

            if matched:
                return "bad_words", text

    return None, None


async def _is_violation(pool, user_id: int, settings: dict, feature_key: str) -> bool:
    """
    يتحقق إن كانت ميزة معينة محظورة عموماً، وأن العضو غير مستثنى منها.
    """
    if not settings.get(feature_key, False):
        return False

    if await protection_queries.is_exempted(pool, user_id, feature_key):
        return False

    return True


async def _delete_later(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)

    try:
        await message.delete()
    except Exception:
        pass
