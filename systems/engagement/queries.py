"""
نظام التفاعل التلقائي (engagement) - الإعدادات.

الإعدادات الجديدة:
- أزرار اختيارية: كل زر يمكن تفعيله/تعطيله
- إيقاف الأوامر النصية بالمجموعة (سوق/عضوية/لقب/مشرف/ادمن/admin)
  وتحويلها للخاص فقط عبر القائمة
"""

import asyncpg

from core.database import get_setting, set_setting


ENGAGEMENT_KEY = "engagement_settings"

DEFAULT_SETTINGS = {
    "enabled": False,
    "interval_seconds": 3600,
    "message_text": "👋 اضغط الزر لفتح قائمتك الشخصية!",
    "button_text": "📋 قائمتي",
    # الأزرار الاختيارية (كلها مفعّلة افتراضياً)
    "btn_account": True,       # 👤 معلوماتي
    "btn_membership": True,    # 👑 عضويتي
    "btn_titles": True,        # 🏷️ ألقابي
    "btn_shop": True,          # 🛒 السوق
    "btn_leaderboard": True,   # 🏆 الترتيب
    "btn_staff_panel": True,   # لوحة المشرف/الأدمن/المالك
    # إيقاف الأوامر النصية بالمجموعة
    "disable_group_commands": False,
}

BUTTON_LABELS = {
    "btn_account": "👤 معلوماتي",
    "btn_membership": "👑 عضويتي",
    "btn_titles": "🏷️ ألقابي",
    "btn_shop": "🛒 السوق",
    "btn_leaderboard": "🏆 الترتيب",
    "btn_staff_panel": "⚙️ لوحة الإدارة",
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


async def toggle_button(pool: asyncpg.Pool, btn_key: str) -> bool:
    settings = await get_engagement_settings(pool)
    settings[btn_key] = not settings.get(btn_key, True)
    await set_engagement_settings(pool, settings)
    return settings[btn_key]


async def toggle_disable_commands(pool: asyncpg.Pool) -> bool:
    settings = await get_engagement_settings(pool)
    settings["disable_group_commands"] = not settings.get("disable_group_commands", False)
    await set_engagement_settings(pool, settings)
    return settings["disable_group_commands"]
