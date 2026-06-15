"""
نظام الحماية (protection) - محرك الفلترة الرئيسي.

يفحص كل رسالة في المجموعة:
1. إذا كانت من المالك/الأدمن/المشرف -> تُعفى تماماً
2. يحدد نوع المحتوى (رابط/ملف/فيديو/صوت/موقع/صورة/ملصق/GIF/نص/جهة اتصال)
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

تم التعديل: إضافة دعم جهات الاتصال + إصلاح ترتيب الفحص + إصلاح الاستثناءات.
"""

import asyncio
import re
import logging

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
logger = logging.getLogger(__name__)


_URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|@\w{4,})",
    re.IGNORECASE,
)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_message(message: Message) -> None:
    """
    الفلتر الرئيسي لكل الرسائل في المجموعة.
    """
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
        # لا توجد مخالفة - نُكمل المعالجة لباقي الأنظمة
        raise SkipHandler

    # ===== تنفيذ الحذف =====
    try:
        await message.delete()
        logger.info(f"تم حذف رسالة من {user_id} بسبب: {violation_type}")
    except Exception as e:
        logger.warning(f"فشل حذف رسالة من {user_id}: {e}")
        raise SkipHandler

    # تسجيل المخالفة
    await protection_queries.log_deleted_message(pool, user_id, violation_type, content_preview)

    # إرسال رسالة تحذير وحذفها بعد فترة
    try:
        warning = await message.answer(messages.VIOLATION_REPLY)
        asyncio.create_task(_delete_later(warning, DEFAULT_DELETE_DELAY))
    except Exception as e:
        logger.warning(f"فشل إرسال رسالة التحذير: {e}")


async def _detect_violation(message: Message, settings: dict, pool, user_id: int) -> tuple[str | None, str | None]:
    """
    يفحص الرسالة ويحدد نوع المخالفة (إن وُجدت) ومعاينة المحتوى.
    
    ترتيب الفحص (من الأكثر خصوصية إلى الأقل):
    1. جهات الاتصال
    2. الموقع الجغرافي
    3. الفيديو
    4. البصمات الصوتية
    5. الملفات
    6. الصور
    7. الملصقات و GIF
    8. النص (روابط + كلمات مسيئة)
    
    يرجع (violation_type, content_preview) أو (None, None) إن لم تكن مخالفة.
    """

    # ===== 1. جهات الاتصال (جديد - أولوية قصوى) =====
    if message.contact is not None:
        if settings.get("contacts", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "contacts")
            if not is_exempt:
                name = message.contact.first_name
                if message.contact.last_name:
                    name += f" {message.contact.last_name}"
                if message.contact.phone_number:
                    name += f" | {message.contact.phone_number}"
                return "contacts", f"جهة اتصال: {name[:100]}"

    # ===== 2. الموقع الجغرافي =====
    if message.location is not None:
        if settings.get("location", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "location")
            if not is_exempt:
                lat = message.location.latitude
                lon = message.location.longitude
                return "location", f"📍 موقع: {lat:.4f}, {lon:.4f}"

    # ===== 3. الفيديو =====
    if message.video is not None:
        if settings.get("videos", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "videos")
            if not is_exempt:
                caption = message.caption or "(فيديو بدون وصف)"
                return "videos", f"🎥 فيديو: {caption[:100]}"

    # ===== 4. البصمات الصوتية (voice notes) =====
    if message.voice is not None:
        if settings.get("voice", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "voice")
            if not is_exempt:
                duration = message.voice.duration
                return "voice", f"🎙️ بصمة صوتية ({duration} ثانية)"

    # ===== 5. الملفات/المستندات =====
    if message.document is not None:
        if settings.get("files", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "files")
            if not is_exempt:
                file_name = message.document.file_name or "(ملف بدون اسم)"
                file_size = message.document.file_size
                return "files", f"📎 {file_name} ({file_size} بايت)"

    # ===== 6. الصور =====
    if message.photo is not None:
        if settings.get("photos", False):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "photos")
            if not is_exempt:
                caption = message.caption or "(صورة بدون وصف)"
                return "photos", f"🖼️ صورة: {caption[:100]}"

    # ===== 7. الملصقات/GIF =====
    if message.sticker is not None:
        if settings.get("stickers_gifs", False):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "stickers_gifs")
            if not is_exempt:
                sticker_emoji = message.sticker.emoji or "بدون إيموجي"
                return "stickers_gifs", f"🎞️ ملصق: {sticker_emoji}"
    
    if message.animation is not None:
        if settings.get("stickers_gifs", False):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "stickers_gifs")
            if not is_exempt:
                caption = message.caption or "(GIF بدون وصف)"
                return "stickers_gifs", f"🎞️ GIF: {caption[:100]}"

    # ===== 8. النص: روابط + كلام مسيء =====
    text = message.text or message.caption

    if text:
        # الروابط
        if settings.get("links", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "links")
            if not is_exempt:
                url_match = _URL_PATTERN.search(text)
                if url_match:
                    return "links", f"🔗 رابط: {url_match.group()[:100]}"

        # الكلام المسيء (باستخدام text_normalizer المحسن)
        if settings.get("bad_words", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "bad_words")
            if not is_exempt:
                banned_words = settings.get("banned_words", [])
                matched = find_matched_word(text, banned_words)

                if matched:
                    # نعرض أول 100 حرف فقط من النص المخالف
                    preview = text[:100] + "..." if len(text) > 100 else text
                    return "bad_words", f"🤬 كلمة محظورة: {matched}\n📝 النص: {preview}"

    return None, None


async def _delete_later(message: Message, delay: int) -> None:
    """
    يحذف رسالة بعد فترة زمنية محددة.
    """
    await asyncio.sleep(delay)

    try:
        await message.delete()
    except Exception as e:
        # نتجاهل الخطأ إذا كانت الرسالة محذوفة بالفعل
        pass