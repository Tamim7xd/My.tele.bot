"""
نظام الإعلانات - التشغيل في المجموعة.

عند كتابة أي عضو لأمر تشغيل إعلان (مثل "قوانين")، يرسل البوت
محتوى الإعلان (نص حالياً، ملف/زر في مرحلة لاحقة)،
ويحذفه تلقائياً بعد المدة المحددة (إن وُجدت).

⚠️ ملاحظة عن الترتيب:
هذا الـ router يستخدم F.text بدون قائمة ثابتة (الأوامر ديناميكية
من قاعدة البيانات)، لذا lookup يحدث لكل رسالة نصية قصيرة. يجب أن
يُسجَّل قبل members_system.router (الذي يطابق كل الرسائل).
لتقليل التكلفة، lookup يتحقق فقط من الرسائل القصيرة (كلمة واحدة)
قبل الاستعلام من قاعدة البيانات.
"""

import asyncio

from aiogram import Router, F
from aiogram.types import Message

from core.database import get_pool
from systems.announcements import queries as announcements_queries


router = Router(name="announcements")


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def trigger_announcement(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    text = message.text.strip()

    # تجاهل سريع: أوامر التشغيل كلمة واحدة بدون مسافات
    if " " in text or len(text) > 30:
        return

    pool = await get_pool()
    ann = await announcements_queries.get_announcement_by_trigger(pool, text)

    if ann is None:
        return

    content_text = ann.get("text") or ""

    sent = await message.answer(content_text) if content_text else None

    delete_after = ann.get("delete_after", 0)

    if delete_after > 0 and sent is not None:
        asyncio.create_task(_delete_later(sent, delete_after))


async def _delete_later(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)

    try:
        await message.delete()
    except Exception:
        pass
