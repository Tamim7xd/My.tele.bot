"""
نظام الحماية - استعلامات قاعدة البيانات
"""

import json
import logging
from typing import Dict, List, Optional

import asyncpg

from core.database import get_setting, set_setting


logger = logging.getLogger(__name__)

PROTECTION_SETTINGS_KEY = "protection_settings"

# قائمة الميزات المدعومة
FEATURE_KEYS = [
    "links", "files", "videos", "voice", "location", 
    "photos", "stickers_gifs", "bad_words", "contacts"
]

FEATURE_LABELS = {
    "links": "🔗 الروابط",
    "files": "📎 الملفات",
    "videos": "🎥 الفيديو",
    "voice": "🎙️ البصمات الصوتية",
    "location": "📍 الموقع",
    "photos": "🖼️ الصور",
    "stickers_gifs": "🎞️ الملصقات/GIF",
    "bad_words": "🤬 الكلام المسيء",
    "contacts": "📇 جهات الاتصال",
}

# الإعدادات الافتراضية - تم تفعيل جميع الميزات
DEFAULT_SETTINGS = {
    "links": True,
    "files": True,
    "videos": True,
    "voice": True,
    "location": True,
    "photos": False,
    "stickers_gifs": False,
    "bad_words": True,
    "contacts": True,
    "banned_words": [],
}


async def get_protection_settings(pool: asyncpg.Pool) -> Dict:
    """جلب إعدادات الحماية"""
    settings = await get_setting(pool, PROTECTION_SETTINGS_KEY, {})
    
    merged = DEFAULT_SETTINGS.copy()
    merged.update(settings)
    
    return merged


async def set_protection_settings(pool: asyncpg.Pool, settings: Dict) -> None:
    """حفظ إعدادات الحماية"""
    await set_setting(pool, PROTECTION_SETTINGS_KEY, settings)


async def toggle_feature(pool: asyncpg.Pool, feature_key: str) -> bool:
    """تبديل حالة ميزة"""
    settings = await get_protection_settings(pool)
    settings[feature_key] = not settings.get(feature_key, False)
    await set_protection_settings(pool, settings)
    return settings[feature_key]


async def add_banned_word(pool: asyncpg.Pool, word: str) -> List[str]:
    """إضافة كلمة محظورة"""
    settings = await get_protection_settings(pool)
    banned_words = settings.get("banned_words", [])
    
    if word not in banned_words:
        banned_words.append(word)
        settings["banned_words"] = banned_words
        await set_protection_settings(pool, settings)
    
    return banned_words


async def remove_banned_word(pool: asyncpg.Pool, word: str) -> List[str]:
    """حذف كلمة محظورة"""
    settings = await get_protection_settings(pool)
    banned_words = settings.get("banned_words", [])
    
    if word in banned_words:
        banned_words.remove(word)
        settings["banned_words"] = banned_words
        await set_protection_settings(pool, settings)
    
    return banned_words


# ==================== الاستثناءات الفردية ====================

async def get_member_exceptions(pool: asyncpg.Pool, user_id: int) -> Dict:
    """جلب استثناءات عضو"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT protection_exceptions FROM members WHERE user_id = $1",
            user_id
        )
    
    if result is None:
        return {}
    
    if isinstance(result, str):
        return json.loads(result)
    
    return result or {}


async def toggle_member_exception(pool: asyncpg.Pool, user_id: int, feature_key: str) -> bool:
    """تبديل استثناء عضو لميزة"""
    exceptions = await get_member_exceptions(pool, user_id)
    exceptions[feature_key] = not exceptions.get(feature_key, False)
    
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET protection_exceptions = $1::jsonb WHERE user_id = $2",
            json.dumps(exceptions), user_id
        )
    
    return exceptions[feature_key]


async def is_exempted(pool: asyncpg.Pool, user_id: int, feature_key: str) -> bool:
    """التحقق من استثناء عضو لميزة معينة"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT protection_exceptions->>$1 FROM members WHERE user_id = $2",
            feature_key, user_id
        )
        return result == "true"


# ==================== سجل المحذوفات ====================

async def log_deleted_message(pool: asyncpg.Pool, user_id: int, violation_type: str, content: Optional[str]) -> None:
    """تسجيل رسالة محذوفة"""
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO protection_log (user_id, violation_type, content) VALUES ($1, $2, $3)",
            user_id, violation_type, content
        )


async def get_violators_with_logs_count(pool: asyncpg.Pool) -> int:
    """عدد المخالفين"""
    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM protection_log")
        return result or 0


async def get_violators_with_logs_list(pool: asyncpg.Pool, offset: int = 0, limit: int = 6) -> List:
    """قائمة المخالفين"""
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT m.user_id, m.username, m.full_name, COUNT(p.id) AS deleted_count
            FROM members m
            JOIN protection_log p ON p.user_id = m.user_id
            GROUP BY m.user_id, m.username, m.full_name
            ORDER BY deleted_count DESC
            OFFSET $1 LIMIT $2
            """,
            offset, limit
        )


async def get_member_deleted_count(pool: asyncpg.Pool, user_id: int) -> int:
    """عدد محذوفات عضو"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM protection_log WHERE user_id = $1",
            user_id
        )
        return result or 0


async def get_member_deleted_entries(pool: asyncpg.Pool, user_id: int, offset: int = 0, limit: int = 5) -> List:
    """سجل محذوفات عضو"""
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT id, violation_type, content, created_at
            FROM protection_log
            WHERE user_id = $1
            ORDER BY created_at DESC
            OFFSET $2 LIMIT $3
            """,
            user_id, offset, limit
        )