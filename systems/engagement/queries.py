"""
نظام التفاعل التلقائي (engagement) - الإعدادات المصلحة والمطورة.
"""

import asyncpg
import uuid
from core.database import get_setting, set_setting

ENGAGEMENT_KEY = "engagement_settings"

# تم تعديل الهيكل ليدعم قائمة رسائل متعددة وسجل التاريخ
DEFAULT_SETTINGS = {
    "enabled": False,
    "interval_seconds": 3600,
    "current_index": 0,
    "messages": [
        {
            "id": "default",
            "message_text": "👋 اضغط الزر لفتح قائمتك الشخصية!",
            "button_text": "📋 قائمتي",
            "button_enabled": True,
            "active": True
        }
    ],
    "history": []
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

# --- الميزات الجديدة المضافة بنفس أسلوب السستم ---

async def add_new_message(pool: asyncpg.Pool, text: str, btn_text: str) -> str:
    settings = await get_engagement_settings(pool)
    msg_id = str(uuid.uuid4())[:6]
    
    new_msg = {
        "id": msg_id,
        "message_text": text,
        "button_text": btn_text,
        "button_enabled": True,
        "active": True
    }
    settings["messages"].append(new_msg)
    await set_engagement_settings(pool, settings)
    return msg_id

async def add_to_engagement_history(pool: asyncpg.Pool, text: str) -> None:
    import datetime
    settings = await get_engagement_settings(pool)
    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    log_entry = f"⏰ [{time_str}] - {text[:30]}..."
    settings["history"].append(log_entry)
    
    # الاحتفاظ بآخر 10 رسائل فقط في السجل لعدم تضخيم البيانات
    settings["history"] = settings["history"][-10:]
    await set_engagement_settings(pool, settings)
