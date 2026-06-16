"""
نظام الحماية (protection) - محرك الفلترة الرئيسي المعدل.
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

# النمط الخاص بالروابط وأرقام الهواتف (لضمان الفحص السريع والمباشر)
_URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)",
    re.IGNORECASE,
)
_PHONE_PATTERN = re.compile(r"(\+?\d{7,15})")


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_message(message: Message) -> None:
    if message.from_user is None:
        raise SkipHandler

    pool = await get_pool()
    user_id = message.from_user.id

    # استثناء المالك/الأدمن/المشرف تلقائياً من أي قيود
    if await permissions.is_staff(pool, user_id):
        raise SkipHandler

    settings = await protection_queries.get_protection_settings(pool)

    # كشف المخالفة بناءً على الإعدادات الحالية
    violation_type, content_preview = await _detect_violation(message, settings, pool, user_id)

    if violation_type is None:
        raise SkipHandler

    # تنفيذ الحذف الفوري للمخالفة
    try:
        await message.delete()
    except Exception:
        raise SkipHandler

    # تسجيل المخالفة في قاعدة البيانات
    await protection_queries.log_deleted_message(pool, user_id, violation_type, content_preview)

    # إرسال رسالة تحذيرية مؤقتة للمخالف وحذفها لاحقاً
    try:
        warning = await message.answer(messages.VIOLATION_REPLY)
        asyncio.create_task(_delete_later(warning, DEFAULT_DELETE_DELAY))
    except Exception:
        pass


async def _detect_violation(
    message: Message, settings: dict, pool, user_id: int
) -> tuple[str | None, str | None]:
    """
    يفحص المحتوى ويتحقق إذا كانت الميزة معطلة عاماً (False) 
    وما إذا كان العضو يملك استثناءً خاصاً لتجاوز هذا التعطيل.
    """

    # ===== 1. الموقع (Location) =====
    if message.location is not None:
        if await _is_violation(pool, user_id, settings, "location"):
            lat = message.location.latitude
            lon = message.location.longitude
            return "location", f"📍 ({lat}, {lon})"

    # ===== 2. جهات الاتصال (Contact) =====
    if message.contact is not None:
        if await _is_violation(pool, user_id, settings, "contact"):
            name = message.contact.first_name or ""
            phone = message.contact.phone_number or ""
            return "contact", f"📞 {name} {phone}".strip()

    # ===== 3. الفيديو (Videos) =====
    if message.video is not None or message.video_note is not None:
        if await _is_violation(pool, user_id, settings, "videos"):
            return "videos", message.caption or "(فيديو / فيديو دائري)"

    # ===== 4. البصمات الصوتية (Voice) =====
    if message.voice is not None or message.audio is not None:
        if await _is_violation(pool, user_id, settings, "voice"):
            return "voice", "(بصمة صوتية / ملف صوتي)"

    # ===== 5. الملفات والمستندات (Files) =====
    if message.document is not None:
        if await _is_violation(pool, user_id, settings, "files"):
            return "files", message.document.file_name or "(ملف)"

    # ===== 6. الصور (Photos) =====
    if message.photo is not None:
        if await _is_violation(pool, user_id, settings, "photos"):
            return "photos", message.caption or "(صورة)"

    # ===== 7. الملصقات والمتحركات (Stickers & GIFs) =====
    if message.sticker is not None or message.animation is not None:
        if await _is_violation(pool, user_id, settings, "stickers_gifs"):
            return "stickers_gifs", "(ملصق / GIF)"

    # ===== 8. النصوص (الروابط، أرقام الهواتف، والكلمات المحظورة) =====
    text = message.text or message.caption

    if text:
        # فحص الروابط
        if await _is_violation(pool, user_id, settings, "links"):
            if _URL_PATTERN.search(text):
                return "links", text[:200]

        # فحص أرقام الهواتف (تعتبر جزء من جهات الاتصال أو الروابط كقيد مضاف)
        if await _is_violation(pool, user_id, settings, "contact"):
            if _PHONE_PATTERN.search(text):
                return "contact", f"(رقم هاتف): {text[:100]}"

        # فحص الكلام المسيء والكلمات المحظورة
        if await _is_violation(pool, user_id, settings, "bad_words"):
            banned_words = settings.get("banned_words", [])
            if banned_words:
                matched = find_matched_word(text, banned_words)
                if matched:
                    return "bad_words", text[:200]

    return None, None


async def _is_violation(pool, user_id: int, settings: dict, feature_key: str) -> bool:
    """
    المنطق الصحيح والمطلوب:
    - البوت يقرأ حالة الميزة (إذا كانت True فهي مسموحة، إذا كانت False فهي معطلة/محظورة داخل المجموعة).
    - إذا كانت الميزة معطلة (False)، يتم التحقق من استثناء العضو.
    - إذا كان العضو مستثنى (True)، يتم السماح له وتخطي الحظر.
    """
    # جلب الإعداد العام (الحالة الافتراضية للميزات هي السماح True إذا لم تكن موجودة)
    is_allowed_globally = settings.get(feature_key, True)

    # إذا كانت الميزة مسموحة للجميع، فلا توجد مخالفة
    if is_allowed_globally:
        return False

    # الميزة معطلة عاماً (False).. الآن نتحقق من الاستثناء الفردي للعضو
    is_user_exempted = await protection_queries.is_exempted(pool, user_id, feature_key)

    # إذا كان العضو مستثنى (مسموح له)، فلا نعتبرها مخالفة له
    if is_user_exempted:
        return False

    # الميزة معطلة عاماً والعضو غير مستثنى -> إذن هي مخالفة ويجب الحذف
    return True


async def _delete_later(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass

