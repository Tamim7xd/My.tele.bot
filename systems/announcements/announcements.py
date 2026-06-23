"""
نظام الإعلانات المتطور - التشغيل في المجموعة.

كل إعلان يمكن أن يحتوي:
- نص (اختياري)
- وسائط: صورة / فيديو / GIF / ملصق (اختياري)
- زر رابط (اختياري)
- تثبيت في المجموعة (اختياري)
- حذف تلقائي بعد مدة (اختياري)

عند كتابة العضو كلمة التشغيل، يُرسَل الإعلان بكل ما يحتويه.
"""

import asyncio

from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool
from systems.announcements import queries as announcements_queries


router = Router(name="announcements")


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def trigger_announcement(message: Message) -> None:
    if message.from_user is None or message.text is None:
        raise SkipHandler

    text = message.text.strip()

    if " " in text or len(text) > 30:
        raise SkipHandler

    pool = await get_pool()
    ann = await announcements_queries.get_announcement_by_trigger(pool, text)

    if ann is None:
        raise SkipHandler

    sent = await _send_announcement(message, ann)

    delete_after = ann.get("delete_after", 0)

    if delete_after > 0 and sent is not None:
        asyncio.create_task(_delete_later(sent, delete_after))

    # تثبيت الرسالة إن طُلب
    if ann.get("pin") and sent is not None:
        try:
            await sent.pin(disable_notification=True)
        except Exception:
            pass


async def _send_announcement(message: Message, ann: dict) -> Message | None:
    """
    يرسل الإعلان بكل محتوياته (نص + وسائط + زر).
    يرجع الرسالة المُرسَلة لاستخدامها في التثبيت/الحذف، أو None عند الفشل.
    """
    content_text = ann.get("text") or ""
    file_id = ann.get("file_id")
    file_type = ann.get("file_type")
    button_text = ann.get("button_text")
    button_url = ann.get("button_url")

    # بناء الكيبورد إن وُجد زر
    keyboard = None
    if button_text and button_url:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=button_text, url=button_url)]
            ]
        )

    try:
        # ملصق (لا يدعم نصاً)
        if file_type == "sticker" and file_id:
            return await message.answer_sticker(sticker=file_id)

        # صورة
        if file_type == "photo" and file_id:
            return await message.answer_photo(
                photo=file_id,
                caption=content_text or None,
                reply_markup=keyboard,
            )

        # فيديو
        if file_type == "video" and file_id:
            return await message.answer_video(
                video=file_id,
                caption=content_text or None,
                reply_markup=keyboard,
            )

        # GIF/animation
        if file_type == "animation" and file_id:
            return await message.answer_animation(
                animation=file_id,
                caption=content_text or None,
                reply_markup=keyboard,
            )

        # نص فقط
        if content_text:
            return await message.answer(content_text, reply_markup=keyboard)

    except Exception:
        pass

    return None


async def _delete_later(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)

    try:
        await message.delete()
    except Exception:
        pass
