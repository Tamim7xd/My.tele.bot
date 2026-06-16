"""
نظام الحماية (protection) - محرك الفلترة الرئيسي.

يفحص كل رسالة في المجموعة، ويحذف المخالفات مع إشعار العضو.
عند عدم وجود مخالفة يرفع SkipHandler لمواصلة المعالجة.
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
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)",
    re.IGNORECASE,
)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_message(message: Message) -> None:
    if message.from_user is None:
        raise SkipHandler

    pool = await get_pool()
    user_id = message.from_user.id

    # استثناء المالك/الأدمن/المشرف
    if await permissions.is_staff(pool, user_id):
        raise SkipHandler

    settings = await protection_queries.get_protection_settings(pool)

    violation_type, content_preview = await _detect_violation(message, settings, pool, user_id)

    if violation_type is None:
        raise SkipHandler

    # تنفيذ الحذف
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


async def _detect_violation(
    message: Message, settings: dict, pool, user_id: int
) -> tuple[str | None, str | None]:
    """
    يفحص كل أنواع المحتوى ويرجع (violation_type, content) أو (None, None).
    """

    # ===== الموقع =====
    if message.location is not None:
        if await _is_violation(pool, user_id, settings, "location"):
            lat = message.location.latitude
            lon = message.location.longitude
            return "location", f"📍 ({lat}, {lon})"

    # ===== جهات الاتصال =====
    if message.contact is not None:
        if await _is_violation(pool, user_id, settings, "contact"):
            name = message.contact.first_name or ""
            phone = message.contact.phone_number or ""
            return "contact", f"📞 {name} {phone}".strip()

    # ===== الفيديو =====
    if message.video is not None:
        if await _is_violation(pool, user_id, settings, "videos"):
            return "videos", message.caption or "(فيديو)"

    # ===== البصمات الصوتية =====
    if message.voice is not None:
        if await _is_violation(pool, user_id, settings, "voice"):
            return "voice", "(بصمة صوتية)"

    # ===== الملفات/المستندات =====
    if message.document is not None:
        if await _is_violation(pool, user_id, settings, "files"):
            return "files", message.document.file_name or "(ملف)"

    # ===== الصور =====
    if message.photo is not None:
        if await _is_violation(pool, user_id, settings, "photos"):
            return "photos", message.caption or "(صورة)"

    # ===== الملصقات/GIF =====
    if message.sticker is not None:
        if await _is_violation(pool, user_id, settings, "stickers_gifs"):
            return "stickers_gifs", "(ملصق)"

    if message.animation is not None:
        if await _is_violation(pool, user_id, settings, "stickers_gifs"):
            return "stickers_gifs", "(GIF)"

    # ===== مقاطع الفيديو القصيرة (video_note) =====
    if message.video_note is not None:
        if await _is_violation(pool, user_id, settings, "videos"):
            return "videos", "(فيديو دائري)"

    # ===== النص: روابط + كلام مسيء =====
    text = message.text or message.caption

    if text:
        if await _is_violation(pool, user_id, settings, "links"):
            if _URL_PATTERN.search(text):
                return "links", text[:200]

        if await _is_violation(pool, user_id, settings, "bad_words"):
            banned_words = settings.get("banned_words", [])
            if banned_words:
                matched = find_matched_word(text, banned_words)
                if matched:
                    return "bad_words", text[:200]

    return None, None


async def _is_violation(pool, user_id: int, settings: dict, feature_key: str) -> bool:
    """
    يتحقق إن كانت الميزة محظورة + العضو غير مستثنى.
    """
    enabled = settings.get(feature_key, False)

    if not enabled:
        return False

    exempted = await protection_queries.is_exempted(pool, user_id, feature_key)

    if exempted:
        return False

    return True


async def _delete_later(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)

    try:
        await message.delete()
    except Exception:
        pass
