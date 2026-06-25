"""
نظام المتجر (shop) - استعلامات/تخزين.

العضويات والألقاب تُخزَّن في settings (إعدادات قابلة للتعديل من اللوحة)،
بينما حالة كل عضو (عضويته الحالية، ألقابه المملوكة) تُخزَّن في جدول members.

===== بنية العضوية الواحدة (membership) =====
{
    "id": "vip", "name": "VIP", "price": 50000, "duration_seconds": 2592000,  # 30 يوم
    "daily_reward": 5000, "can_clear_chat": true, "can_send_media": true,
    "no_replies": false   # فقط Super VIP: يمنع رد الأعضاء العاديين عليه
}

===== بنية اللقب الواحد (title) =====
{"id": "title1", "name": "🔥 الأسطورة", "price": 10000}
"""

import asyncpg

from core.database import get_setting, set_setting


MEMBERSHIPS_KEY = "shop_memberships"
TITLES_KEY = "shop_titles"
CLEAR_CHAT_PRICE_KEY = "shop_clear_chat_price"
CLEAR_CHAT_RANGE_KEY = "shop_clear_chat_range"

DEFAULT_CLEAR_CHAT_PRICE = 1000
DEFAULT_CLEAR_CHAT_RANGE = 100

DEFAULT_MEMBERSHIPS = [
    {
        "id": "vip", "name": "VIP", "price": 50000, "duration_seconds": 2592000,  # 30 يوم
        "daily_reward": 5000, "can_clear_chat": True, "can_send_media": True,
        "no_replies": False,
        "clear_cooldown_seconds": 300,
    },
    {
        "id": "gold", "name": "🥇 Gold", "price": 75000, "duration_seconds": 2592000,  # 30 يوم
        "daily_reward": 5000, "can_clear_chat": True, "can_send_media": True,
        "no_replies": False,
        "clear_cooldown_seconds": 300,
    },
    {
        "id": "platinum", "name": "💎 Platinum", "price": 100000, "duration_seconds": 2592000,  # 30 يوم
        "daily_reward": 5000, "can_clear_chat": True, "can_send_media": True,
        "no_replies": False,
        "clear_cooldown_seconds": 300,
    },
    {
        "id": "elite", "name": "⭐ Elite", "price": 125000, "duration_seconds": 2592000,  # 30 يوم
        "daily_reward": 5000, "can_clear_chat": True, "can_send_media": True,
        "no_replies": False,
        "clear_cooldown_seconds": 300,
    },
    {
        "id": "super_vip", "name": "👑 Super VIP", "price": 200000, "duration_seconds": 2592000,  # 30 يوم
        "daily_reward": 5000, "can_clear_chat": True, "can_send_media": True,
        "no_replies": True,
        "clear_cooldown_seconds": 300,
    },
]

DEFAULT_TITLES = [
    {"id": "title1", "name": "🔥 الأسطورة", "price": 10000},
    {"id": "title2", "name": "⚡ المحارب", "price": 10000},
    {"id": "title3", "name": "🌟 النجم", "price": 10000},
    {"id": "title4", "name": "🦁 الأسد", "price": 10000},
]


# ===== العضويات =====

async def get_memberships(pool: asyncpg.Pool) -> list[dict]:
    return await get_setting(pool, MEMBERSHIPS_KEY, DEFAULT_MEMBERSHIPS)


async def set_memberships(pool: asyncpg.Pool, memberships: list[dict]) -> None:
    await set_setting(pool, MEMBERSHIPS_KEY, memberships)


async def get_membership_by_id(pool: asyncpg.Pool, membership_id: str) -> dict | None:
    memberships = await get_memberships(pool)

    for m in memberships:
        if m["id"] == membership_id:
            return m

    return None


async def update_membership(pool: asyncpg.Pool, membership_id: str, updated: dict) -> None:
    memberships = await get_memberships(pool)

    for i, m in enumerate(memberships):
        if m["id"] == membership_id:
            memberships[i] = updated
            break

    await set_memberships(pool, memberships)


# ===== الألقاب =====

async def get_titles(pool: asyncpg.Pool) -> list[dict]:
    return await get_setting(pool, TITLES_KEY, DEFAULT_TITLES)


async def set_titles(pool: asyncpg.Pool, titles: list[dict]) -> None:
    await set_setting(pool, TITLES_KEY, titles)


async def get_title_by_id(pool: asyncpg.Pool, title_id: str) -> dict | None:
    titles = await get_titles(pool)

    for t in titles:
        if t["id"] == title_id:
            return t

    return None


async def update_title(pool: asyncpg.Pool, title_id: str, updated: dict) -> None:
    titles = await get_titles(pool)

    for i, t in enumerate(titles):
        if t["id"] == title_id:
            titles[i] = updated
            break

    await set_titles(pool, titles)


# ===== مسح المحادثة (clear chat) =====

async def get_clear_chat_price(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, CLEAR_CHAT_PRICE_KEY, DEFAULT_CLEAR_CHAT_PRICE)


async def set_clear_chat_price(pool: asyncpg.Pool, price: int) -> None:
    await set_setting(pool, CLEAR_CHAT_PRICE_KEY, price)


async def get_clear_chat_range(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, CLEAR_CHAT_RANGE_KEY, DEFAULT_CLEAR_CHAT_RANGE)


async def set_clear_chat_range(pool: asyncpg.Pool, range_count: int) -> None:
    await set_setting(pool, CLEAR_CHAT_RANGE_KEY, range_count)


def format_duration(seconds: int) -> str:
    """يحول عدد الثواني لنص عربي مقروء (للعرض في تفاصيل العضوية)."""
    if seconds <= 0:
        return "بلا انتهاء (دائمة)"

    if seconds % 2592000 == 0:
        months = seconds // 2592000
        return f"{months} شهر" if months == 1 else f"{months} أشهر"

    if seconds % 86400 == 0:
        days = seconds // 86400
        return f"{days} يوم" if days == 1 else f"{days} أيام"

    if seconds % 3600 == 0:
        hours = seconds // 3600
        return f"{hours} ساعة" if hours == 1 else f"{hours} ساعات"

    if seconds % 60 == 0:
        minutes = seconds // 60
        return f"{minutes} دقيقة" if minutes == 1 else f"{minutes} دقائق"

    return f"{seconds} ثانية"
