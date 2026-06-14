"""
نظام الحظر/الكتم/التحذير - المجدول التلقائي.

يفحص دورياً (كل دقيقة) الأعضاء الذين انتهت مدة كتمهم/حظرهم،
ويقوم بـ:
- رفع الكتم/الحظر في قاعدة البيانات
- محاولة رفعه فعلياً في تيليجرام
- إشعار المجموعة + رسالة خاصة للعضو

moderation_scheduler_loop يُستدعى من core/bot.py مرة واحدة عند بدء التشغيل
(كـ asyncio task مستقل، لا يوقف عمل البوت).
"""

import asyncio

from aiogram import Bot
from aiogram.types import ChatPermissions

from core.database import get_pool
from systems.moderation import queries as moderation_queries
from systems.moderation.notifications import messages


CHECK_INTERVAL_SECONDS = 60


async def _check_expired(bot: Bot, group_id: int | None) -> None:
    pool = await get_pool()

    # ===== الكتم المنتهي =====
    for row in await moderation_queries.get_expired_mutes(pool):
        await moderation_queries.unmute(pool, row["user_id"])

        if group_id:
            try:
                await bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=row["user_id"],
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_audios=True,
                        can_send_documents=True,
                        can_send_photos=True,
                        can_send_videos=True,
                        can_send_video_notes=True,
                        can_send_voice_notes=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                    ),
                )
            except Exception:
                pass

            try:
                await bot.send_message(
                    chat_id=group_id,
                    text=messages.mute_expired_notification(row["full_name"], row["username"]),
                )
            except Exception:
                pass

        try:
            await bot.send_message(chat_id=row["user_id"], text=messages.MUTE_EXPIRED_PRIVATE)
        except Exception:
            pass

    # ===== الحظر المنتهي =====
    for row in await moderation_queries.get_expired_bans(pool):
        await moderation_queries.unban(pool, row["user_id"])

        if group_id:
            try:
                await bot.unban_chat_member(chat_id=group_id, user_id=row["user_id"], only_if_banned=True)
            except Exception:
                pass

            try:
                await bot.send_message(
                    chat_id=group_id,
                    text=messages.ban_expired_notification(row["full_name"], row["username"]),
                )
            except Exception:
                pass

        try:
            await bot.send_message(chat_id=row["user_id"], text=messages.BAN_EXPIRED_PRIVATE)
        except Exception:
            pass


async def moderation_scheduler_loop(bot: Bot, group_id: int | None) -> None:
    """حلقة لا نهائية تفحص الكتم/الحظر المنتهي كل دقيقة."""
    while True:
        try:
            await _check_expired(bot, group_id)
        except Exception:
            pass

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
