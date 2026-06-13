"""
نظام الإداريين - الصلاحيات.

يحتوي على:
- الصلاحيات الثابتة الافتراضية لكل رتبة (member / moderator / admin / owner)
- دالة has_permission التي تتحقق من صلاحية معينة لعضو معين،
  مع الأخذ بالاعتبار التخصيص الإضافي المخزّن في عمود permissions (JSONB)
- دالة can_act_on التي تتحقق من التسلسل الهرمي بين عضوين

أي نظام يريد التحقق من صلاحية يستورد هذا الملف:

    from systems.moderators import permissions

    if await permissions.has_permission(pool, user_id, "mute"):
        ...

    if await permissions.can_act_on(pool, actor_id, target_id):
        ...
"""

import json

import asyncpg

from core.config import OWNER_ID


# ===== الصلاحيات الثابتة الافتراضية لكل رتبة =====
DEFAULT_PERMISSIONS: dict[str, set[str]] = {
    "member": set(),
    "moderator": {"mute", "deduct", "warn"},
    "admin": {"mute", "deduct", "ban", "reward", "warn"},
    "owner": {"mute", "deduct", "ban", "reward", "warn", "all"},
}


RANKS_ORDER = ["member", "moderator", "admin", "owner"]


async def get_permissions(pool: asyncpg.Pool, user_id: int) -> set[str]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT rank, permissions FROM members WHERE user_id = $1",
            user_id,
        )

    if row is None:
        return set()

    rank = row["rank"] or "member"
    custom_raw = row["permissions"] or "{}"

    if isinstance(custom_raw, str):
        custom = json.loads(custom_raw)
    else:
        custom = custom_raw

    base = set(DEFAULT_PERMISSIONS.get(rank, set()))

    added = set(custom.get("add", []))
    removed = set(custom.get("remove", []))

    return (base | added) - removed


async def has_permission(pool: asyncpg.Pool, user_id: int, permission: str) -> bool:
    if user_id == OWNER_ID:
        return True

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
    if user_id == OWNER_ID:
        return True

    async with pool.acquire() as conn:
        rank = await conn.fetchval(
            "SELECT rank FROM members WHERE user_id = $1",
            user_id,
        )

    return rank in ("moderator", "admin", "owner")


async def get_user_rank(pool: asyncpg.Pool, user_id: int) -> str:
    """
    يرجع رتبة العضو الفعلية.
    OWNER_ID (من .env) يُعتبر دائماً "owner" حتى لو لم يُحدَّث في قاعدة البيانات.
    """
    if user_id == OWNER_ID:
        return "owner"

    async with pool.acquire() as conn:
        rank = await conn.fetchval(
            "SELECT rank FROM members WHERE user_id = $1",
            user_id,
        )

    return rank or "member"


async def can_act_on(pool: asyncpg.Pool, actor_id: int, target_id: int) -> bool:
    """
    يتحقق إن كان actor_id يستطيع تنفيذ إجراء (خصم/مكافأة/كتم/حظر/تحذير)
    على target_id، بناءً على التسلسل الهرمي للرتب:

        owner > admin > moderator > member

    القاعدة: لا يمكن لعضو تنفيذ إجراء على عضو برتبة أعلى أو مساوية له،
    إلا المالك (owner) الذي يستطيع التصرف على أي شخص بما فيهم نفسه.
    """
    actor_rank = await get_user_rank(pool, actor_id)

    if actor_rank == "owner":
        return True

    target_rank = await get_user_rank(pool, target_id)

    actor_level = RANKS_ORDER.index(actor_rank)
    target_level = RANKS_ORDER.index(target_rank)

    return actor_level > target_level