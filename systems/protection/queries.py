"""
نظام الحماية (protection) - استعلامات/تخزين.
"""

import json

import asyncpg

from core.database import get_setting, set_setting


PROTECTION_SETTINGS_KEY = "protection_settings"
SYSTEM_WORDS_KEY = "protection_system_words"

FEATURE_KEYS = [
    "links", "files", "videos", "voice", "location", "contact",
    "photos", "stickers_gifs", "bad_words", "phone_numbers", "forwarded",
]

FEATURE_LABELS = {
    "links": "🔗 الروابط",
    "files": "📎 الملفات",
    "videos": "🎥 الفيديو",
    "voice": "🎙️ البصمات الصوتية",
    "location": "📍 الموقع",
    "contact": "📞 جهات الاتصال",
    "photos": "🖼️ الصور",
    "stickers_gifs": "🎞️ الملصقات/GIF",
    "bad_words": "🤬 الكلام المسيء",
    "phone_numbers": "☎️ أرقام الهواتف",
    "forwarded": "↪️ الرسائل الموجّهة",
}

DEFAULT_SETTINGS = {
    "links": True,
    "files": True,
    "videos": True,
    "voice": True,
    "location": True,
    "contact": True,
    "photos": False,
    "stickers_gifs": False,
    "bad_words": True,
    "phone_numbers": True,
    "forwarded": False,
    "block_bots": True,
    "banned_words": [],
}


async def get_protection_settings(pool: asyncpg.Pool) -> dict:
    """
    يرجع إعدادات الحماية الحالية.
    ⚠️ مهم: يجمع ONLY القيم المخزنة في DB مع الإعدادات الافتراضية
    للمفاتيح الناقصة فقط - لا يُعيد كتابة قيم موجودة بالفعل.
    """
    stored = await get_setting(pool, PROTECTION_SETTINGS_KEY, None)

    if stored is None:
        # أول تشغيل - نحفظ القيم الافتراضية ونرجعها
        await set_setting(pool, PROTECTION_SETTINGS_KEY, DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    # دمج آمن: القيم المخزنة تتجاوز الافتراضية
    merged = dict(DEFAULT_SETTINGS)
    if isinstance(stored, dict):
        merged.update(stored)

    return merged


async def set_protection_settings(pool: asyncpg.Pool, settings: dict) -> None:
    """يحفظ إعدادات الحماية بالكامل (يستبدل الموجود)."""
    await set_setting(pool, PROTECTION_SETTINGS_KEY, settings)


# ===== خيارات النظام (قائمة كلمات منفصلة، يديرها المالك بالكامل) =====

async def get_system_words(pool: asyncpg.Pool) -> list[str]:
    return await get_setting(pool, SYSTEM_WORDS_KEY, [])


async def set_system_words(pool: asyncpg.Pool, words: list[str]) -> None:
    await set_setting(pool, SYSTEM_WORDS_KEY, words)


async def add_system_word(pool: asyncpg.Pool, word: str) -> list[str]:
    words = await get_system_words(pool)

    if word not in words:
        words.append(word)
        await set_system_words(pool, words)

    return words


async def remove_system_word(pool: asyncpg.Pool, word: str) -> list[str]:
    words = await get_system_words(pool)

    if word in words:
        words.remove(word)
        await set_system_words(pool, words)

    return words


async def toggle_feature(pool: asyncpg.Pool, feature_key: str) -> bool:
    """
    يبدّل حالة ميزة واحدة (تشغيل/إيقاف).
    ⚠️ مهم: يقرأ الإعدادات الحالية أولاً، يعدّل المفتاح المطلوب فقط،
    ثم يحفظ الكل - بدون المساس بباقي الإعدادات.
    يرجع الحالة الجديدة (True=محظور, False=مسموح).
    """
    settings = await get_protection_settings(pool)

    current = settings.get(feature_key, DEFAULT_SETTINGS.get(feature_key, False))
    settings[feature_key] = not current

    await set_protection_settings(pool, settings)

    return settings[feature_key]


async def add_banned_word(pool: asyncpg.Pool, word: str) -> list[str]:
    settings = await get_protection_settings(pool)
    banned_words = settings.get("banned_words", [])

    if word not in banned_words:
        banned_words.append(word)
        settings["banned_words"] = banned_words
        await set_protection_settings(pool, settings)

    return banned_words


async def remove_banned_word(pool: asyncpg.Pool, word: str) -> list[str]:
    settings = await get_protection_settings(pool)
    banned_words = settings.get("banned_words", [])

    if word in banned_words:
        banned_words.remove(word)
        settings["banned_words"] = banned_words
        await set_protection_settings(pool, settings)

    return banned_words


# ===== الاستثناءات الفردية =====

async def get_member_exceptions(pool: asyncpg.Pool, user_id: int) -> dict:
    """يرجع استثناءات عضو معين (True = مسموح له بتجاوز الحظر)."""
    async with pool.acquire() as conn:
        raw = await conn.fetchval(
            "SELECT protection_exceptions FROM members WHERE user_id = $1", user_id
        )

    if raw is None:
        return {}

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}

    if isinstance(raw, dict):
        return raw

    return {}


async def toggle_member_exception(pool: asyncpg.Pool, user_id: int, feature_key: str) -> bool:
    """
    يبدّل استثناء عضو لميزة معينة.
    True = مسموح له بتجاوز الحظر، False = يخضع للإعداد العام.
    يرجع الحالة الجديدة.
    """
    exceptions = await get_member_exceptions(pool, user_id)
    exceptions[feature_key] = not exceptions.get(feature_key, False)

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET protection_exceptions = $1::jsonb WHERE user_id = $2",
            json.dumps(exceptions), user_id,
        )

    return exceptions[feature_key]


async def is_exempted(pool: asyncpg.Pool, user_id: int, feature_key: str) -> bool:
    """يتحقق إن كان عضو معين مستثنى من قيد ميزة معينة."""
    exceptions = await get_member_exceptions(pool, user_id)
    return exceptions.get(feature_key, False)


# ===== سجل المحذوفات (protection_log) =====

async def log_deleted_message(pool: asyncpg.Pool, user_id: int, violation_type: str, content: str | None) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO protection_log (user_id, violation_type, content) VALUES ($1, $2, $3)",
            user_id, violation_type, content,
        )


async def get_violators_with_logs_count(pool: asyncpg.Pool) -> int:
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(DISTINCT user_id) FROM protection_log"
        )
        return result or 0


async def get_violators_with_logs_list(pool: asyncpg.Pool, offset: int = 0, limit: int = 6) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT
                m.user_id, m.username, m.full_name,
                COUNT(p.id) AS deleted_count
            FROM members m
            JOIN protection_log p ON p.user_id = m.user_id
            GROUP BY m.user_id, m.username, m.full_name
            ORDER BY deleted_count DESC
            OFFSET $1 LIMIT $2
            """,
            offset, limit,
        )


async def get_member_deleted_count(pool: asyncpg.Pool, user_id: int) -> int:
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM protection_log WHERE user_id = $1", user_id
        )
        return result or 0


async def get_member_deleted_entries(pool: asyncpg.Pool, user_id: int, offset: int = 0, limit: int = 5) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT id, violation_type, content, created_at
            FROM protection_log
            WHERE user_id = $1
            ORDER BY created_at DESC
            OFFSET $2 LIMIT $3
            """,
            user_id, offset, limit,
        )
