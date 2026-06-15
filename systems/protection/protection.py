"""
نظام الحماية - النسخة الكاملة والمضمونة
يدعم: الموقع، جهات الاتصال، الصور، الفيديو، الملفات، البصمات، الكلمات المحظورة
"""

import asyncio
import re
import logging
from typing import Optional, Tuple

from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message

from core.database import get_pool
from core.config import DEFAULT_DELETE_DELAY
from systems.moderators import permissions
from systems.protection import queries as protection_queries
from systems.protection.text_normalizer import find_matched_word


router = Router(name="protection")
logger = logging.getLogger(__name__)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_message(message: Message) -> None:
    """
    الفلتر الرئيسي - يفحص كل الرسائل في المجموعة
    """
    if message.from_user is None:
        raise SkipHandler

    user_id = message.from_user.id
    pool = await get_pool()

    # ===== 1. استثناء المالك/الأدمن/المشرف =====
    if await permissions.is_staff(pool, user_id):
        raise SkipHandler

    # ===== 2. جلب الإعدادات =====
    settings = await protection_queries.get_protection_settings(pool)

    # ===== 3. فحص المخالفة =====
    violation_type, content_preview = await check_message(
        message=message,
        settings=settings,
        pool=pool,
        user_id=user_id
    )

    # ===== 4. إذا لم توجد مخالفة =====
    if violation_type is None:
        raise SkipHandler

    # ===== 5. حذف الرسالة المخالفة =====
    try:
        await message.delete()
        logger.info(f"✅ تم حذف {violation_type} من {user_id}")
        
        # تسجيل المخالفة
        await protection_queries.log_deleted_message(pool, user_id, violation_type, content_preview)
        
        # إرسال رسالة تحذير
        warning_msg = await message.answer(f"🚫 ممنوع - هذا المحتوى غير مسموح به")
        asyncio.create_task(delete_later(warning_msg, DEFAULT_DELETE_DELAY))
        
    except Exception as e:
        logger.error(f"فشل حذف الرسالة: {e}")


async def check_message(
    message: Message,
    settings: dict,
    pool,
    user_id: int
) -> Tuple[Optional[str], Optional[str]]:
    """
    فحص الرسالة وتحديد نوع المخالفة
    """
    
    # ----- 1. جهة الاتصال (أعلى أولوية) -----
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
    
    # ----- 2. الموقع الجغرافي -----
    if message.location is not None:
        if settings.get("location", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "location")
            if not is_exempt:
                lat = message.location.latitude
                lon = message.location.longitude
                return "location", f"📍 موقع: {lat:.4f}, {lon:.4f}"
    
    # ----- 3. الفيديو -----
    if message.video is not None:
        if settings.get("videos", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "videos")
            if not is_exempt:
                caption = message.caption or "(فيديو بدون وصف)"
                return "videos", f"🎥 فيديو: {caption[:100]}"
    
    # ----- 4. البصمات الصوتية -----
    if message.voice is not None:
        if settings.get("voice", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "voice")
            if not is_exempt:
                duration = message.voice.duration
                return "voice", f"🎙️ بصمة صوتية ({duration} ثانية)"
    
    # ----- 5. الملفات -----
    if message.document is not None:
        if settings.get("files", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "files")
            if not is_exempt:
                file_name = message.document.file_name or "(ملف بدون اسم)"
                file_size = message.document.file_size
                return "files", f"📎 {file_name} ({file_size} بايت)"
    
    # ----- 6. الصور -----
    if message.photo is not None:
        if settings.get("photos", False):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "photos")
            if not is_exempt:
                caption = message.caption or "(صورة بدون وصف)"
                return "photos", f"🖼️ صورة: {caption[:100]}"
    
    # ----- 7. الملصقات و GIF -----
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
    
    # ----- 8. النص -----
    text = message.text or message.caption
    if text:
        # الروابط
        if settings.get("links", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "links")
            if not is_exempt:
                url_pattern = re.compile(r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)", re.IGNORECASE)
                url_match = url_pattern.search(text)
                if url_match:
                    return "links", f"🔗 رابط: {url_match.group()[:100]}"
        
        # الكلمات المسيئة
        if settings.get("bad_words", True):
            is_exempt = await protection_queries.is_exempted(pool, user_id, "bad_words")
            if not is_exempt:
                banned_words = settings.get("banned_words", [])
                if banned_words:
                    matched = find_matched_word(text, banned_words)
                    if matched:
                        preview = text[:100] + "..." if len(text) > 100 else text
                        return "bad_words", f"🤬 كلمة محظورة: {matched}\n📝 النص: {preview}"
    
    return None, None


async def delete_later(message: Message, delay: int):
    """حذف رسالة بعد فترة زمنية"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass