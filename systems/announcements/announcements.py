"""
نظام الإعلانات المتطور - التشغيل في المجموعة.

كل إعلان يمكن أن يحتوي:
- نص (اختياري)
- وسائط: صورة / فيديو / GIF / ملصق (اختياري)
- زر رابط (اختياري)
- تثبيت في المجموعة (اختياري)
- حذف تلقائي بعد مدة (اختياري)

عند كتابة العضو كلمة التشغيل، يُرسَل الإعلان بكل ما يحتوي.
"""

import asyncio
import logging

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool
from systems.announcements import queries as announcements_queries

# إعداد السجلات لطباعة الأخطاء في الـ Console في حال فشل الإرسال
logger = logging.getLogger(__name__)
router = Router(name="announcements")


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def trigger_announcement(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    # تنظيف النص من الفراغات الزائدة في البداية والنهاية
    text = message.text.strip()

    # إذا كان النص فارغاً أو طويلاً جداً كأمر تشغيل، يتم إيقاف المعالج بدلاً من تمريره
    if not text or len(text) > 50:
        return

    pool = await get_pool()
    # جلب الإعلان بناءً على الكلمة المستلمة (البحث عن مطابقة تامة بعد التنظيف)
    ann = await announcements_queries.get_announcement_by_trigger(pool, text)

    # إذا لم يتم العثور على إعلان مطابخ، يتم إنهاء الدالة بهدوء دون التأثير على المعالجات الأخرى
    if ann is None:
        return

    # محاولة إرسال الإعلان
    sent = await _send_announcement(message, ann)

    if sent is None:
        return

    # حذف الرسالة تلقائياً إن طُلب ذلك
    delete_after = ann.get("delete_after", 0)
    if delete_after > 0:
        asyncio.create_task(_delete_later(sent, delete_after))

    # تثبيت الرسالة إن طُلب وكان البوت يمتلك الصلاحية
    if ann.get("pin"):
        try:
            await sent.pin(disable_notification=True)
        except Exception as e:
            logger.warning(f"Failed to pin message: {e}")


async def _send_announcement(message: Message, ann: dict) -> Message | None:
    """
    يرسل الإعلان بكل محتوياته (نص + وسائط + زر).
    يرجع الرسالة المُرسَلة لاستخدامها في التثبيت/الحذف، أو None عند الفشل مع طباعة السبب.
    """
    content_text = ann.get("text") or ""
    file_id = ann.get("file_id")
    file_type = ann.get("file_type")
    button_text = ann.get("button_text")
    button_url = ann.get("button_url")

    # بناء الكيبورد إن وُجد زر رابط
    keyboard = None
    if button_text and button_url:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=button_text, url=button_url)]
            ]
        )

    try:
        # 1. ملصق (لا يدعم نصوصاً توضيحية)
        if file_type == "sticker" and file_id:
            return await message.answer_sticker(sticker=file_id)

        # 2. صورة
        if file_type == "photo" and file_id:
            return await message.answer_photo(
                photo=file_id,
                caption=content_text or None,
                reply_markup=keyboard,
            )

        # 3. فيديو
        if file_type == "video" and file_id:
            return await message.answer_video(
                video=file_id,
                caption=content_text or None,
                reply_markup=keyboard,
            )

        # 4. رسالة متحركة GIF
        if file_type == "animation" and file_id:
            return await message.answer_animation(
                animation=file_id,
                caption=content_text or None,
                reply_markup=keyboard,
            )

        # 5. نص فقط (في حال عدم وجود أي وسائط)
        if content_text:
            return await message.answer(content_text, reply_markup=keyboard)

    except Exception as e:
        # طباعة الخطأ في الـ Console إذا فشل الإرسال (مثلاً بسبب file_id خاطئ أو نقص صلاحيات)
        logger.error(f"Error sending announcement (Trigger: {ann.get('trigger')}): {e}")

    return None


async def _delete_later(message: Message, delay: int) -> None:
    """حذف الرسالة بعد مرور الوقت المحدد."""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass
