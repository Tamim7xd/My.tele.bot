"""
نظام الإداريين - الصلاحيات.

يحتوي على:
- الصلاحيات الثابتة الافتراضية لكل رتبة (member / moderator / admin / owner)
- دالة has_permission التي تتحقق من صلاحية معينة لعضو معين،
  مع الأخذ بالاعتبار التخصيص الإضافي المخزّن في عمود permissions (JSONB)

أي نظام يريد التحقق من صلاحية يستورد هذا الملف:

    from systems.moderators import permissions

    if await permissions.has_permission(pool, user_id, "mute"):
        ...
"""

import asyncpg


# ===== الصلاحيات الثابتة الافتراضية لكل رتبة =====
# يمكن لكل عضو أن يحصل على صلاحيات إضافية أو إزالة صلاحية معينة
# عبر عمود permissions (JSONB) في جدول members، والذي يتم دمجه
# مع هذه القيم الافتراضية.

DEFAULT_PERMISSIONS: dict[str, set[str]] = {
    "member": set(),
    "moderator": {"mute", "deduct", "warn"},
    "admin": {"mute", "deduct", "ban", "reward", "warn"},
    "owner": {"mute", "deduct", "ban", "reward", "warn", "all"},
}


RANKS_ORDER = ["member", "moderator", "admin", "owner"]


async def get_permissions(pool: asyncpg.Pool, user_id: int) -> set[str]:
    """
    يرجع مجموعة الصلاحيات الفعلية لعضو معين:
    الصلاحيات الافتراضية لرتبته + الإضافات - المُزالات
    (المخصصات مخزّنة في عمود permissions كـ JSONB بالشكل:
     {"add": [...], "remove": [...]})
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT rank, permissions FROM members WHERE user_id = $1",
            user_id,
        )

    if row is None:
        return set()

    rank = row["rank"] or "member"
    custom = row["permissions"] or {}

    base = set(DEFAULT_PERMISSIONS.get(rank, set()))

    added = set(custom.get("add", []))
    removed = set(custom.get("remove", []))

    return (base | added) - removed


async def has_permission(pool: asyncpg.Pool, user_id: int, permission: str) -> bool:
    """
    يتحقق إن كان لدى العضو صلاحية معينة.
    "owner" و "all" يتجاوزان أي تحقق (صلاحية كاملة).
    """
    async with pool.acquire() as conn:
        rank = await conn.fetchval(
            "SELECT rank FROM members WHERE user_id = $1",
            user_id,
        )

    if rank == "owner":
        return True

    perms = await get_permissions(pool, user_id)

    return "all" in perms or permission in perms


async def is_staff(pool: asyncpg.Pool, user_id: int) -> bool:
    """يتحقق إن كان العضو مشرف/أدمن/مالك (أي رتبة أعلى من عضو عادي)."""
    async with pool.acquire() as conn:
        rank = await conn.fetchval(
            "SELECT rank FROM members WHERE user_id = $1",
            user_id,
        )

    return rank in ("moderator", "admin", "owner")
