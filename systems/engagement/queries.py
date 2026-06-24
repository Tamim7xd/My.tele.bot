"""
نظام التفاعل التلقائي (engagement) - الإعدادات.

البوت يرسل رسالة دورية في المجموعة بزر، عند الضغط تُفتح
قائمة أوامر العضو في الخاص حسب رتبته:
- عضو عادي: معلومات، عضوية، لقب، سوق، ترتيب
- مشرف/أدمن: نفس الأعلى + زر لوحة المشرف/الأدمن
- المالك: نفس الأعلى + زر لوحة التحكم الكاملة
"""

import asyncpg

from core.database import get_setting, set_setting


ENGAGEMENT_KEY = "engagement_settings"

DEFAULT_SETTINGS = {
    "enabled": False,
    "interval_seconds": 3600,
    "message_text": "👋 اضغط الزر لفتح قائمتك الشخصية!",
    "button_text": "📋 قائمتي",
}


async def get_engagement_settings(pool: asyncpg.Pool) -> dict:
    stored = await get_setting(pool, ENGAGEMENT_KEY, None)

    if stored is None:
        await set_setting(pool, ENGAGEMENT_KEY, DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    merged = dict(DEFAULT_SETTINGS)
    if isinstance(stored, dict):
        merged.update(stored)

    return merged


async def set_engagement_settings(pool: asyncpg.Pool, settings: dict) -> None:
    await set_setting(pool, ENGAGEMENT_KEY, settings)


async def toggle_engagement(pool: asyncpg.Pool) -> bool:
    settings = await get_engagement_settings(pool)
    settings["enabled"] = not settings.get("enabled", False)
    await set_engagement_settings(pool, settings)
    return settings["enabled"]
