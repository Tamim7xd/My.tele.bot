import asyncio
import json
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.db import get_pool # ممر الاتصال الخاص بك
from systems.engagement import queries as engagement_queries

async def _send_next_engagement_message(bot: Bot) -> None:
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    
    # جلب معرف المجموعه المستهدفة المخرن بالنظام لديك
    group_id = settings.get("group_id") 
    if not group_id:
        return

    active_messages = await engagement_queries.get_active_messages(pool)
    if not active_messages:
        return # لا توجد رسائل نشطة لإرسالها حالياً

    # نظام التدوير الذكي (Round-Robin)
    last_index = settings.get("last_index", 0)
    if last_index >= len(active_messages):
        last_index = 0

    msg_to_send = active_messages[last_index]
    
    # بناء الأزرار إن وجدت وتأكيد عدم تعطيلها
    reply_markup = None
    if msg_to_send.get("buttons"):
        try:
            btn_data = json.loads(msg_to_send["buttons"])
            if btn_data: # إذا لم تكن الأزرار فارغة أو معطلة
                keyboard = []
                for btn in btn_data:
                    keyboard.append([InlineKeyboardButton(text=btn['text'], url=btn['url'])])
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        except Exception:
            reply_markup = None

    try:
        await bot.send_message(
            chat_id=group_id,
            text=msg_to_send["text"],
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        # تحديث المؤشر للرسالة التالية في المرة القادمة
        next_index = (last_index + 1) % len(active_messages)
        await engagement_queries.update_setting(pool, "last_index", next_index)
    except Exception as e:
        print(f"Error sending engagement message: {e}")

async def engagement_scheduler_loop(bot: Bot) -> None:
    """الحلقة المصلحة بالكامل لضمان عدم النوم اللانهائي عند الإضافة أو التفعيل"""
    while True:
        pool = await get_pool()
        settings = await engagement_queries.get_engagement_settings(pool)
        
        if settings.get("enabled", False):
            active_messages = await engagement_queries.get_active_messages(pool)
            if active_messages:
                await _send_next_engagement_message(bot)
                interval = settings.get("interval_seconds", 3600)
                await asyncio.sleep(max(interval, 10))
                continue
        
        # إذا كان النظام معطلاً أو السجل فارغاً، ينام 20 ثانية فقط ليفحص مجدداً بشكل سريع فور التفعيل
        await asyncio.sleep(20)
