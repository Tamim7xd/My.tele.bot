import json
from typing import List, Dict, Any, Optional
from asyncpg import Pool

# إنشاء الجداول الجديدة لدعم تعدد الرسائل وسجل الحالات
async def init_db(pool: Pool):
    async with pool.acquire() as conn:
        # جدول الإعدادات العامة
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS engagement_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # جدول سجل الرسائل المتعددة
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS engagement_messages (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                buttons TEXT, -- تخزن كـ JSON
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

async def get_engagement_settings(pool: Pool) -> Dict[str, Any]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT key, value FROM engagement_settings")
        settings = {row["key"]: json.loads(row["value"]) for row in rows}
        # قيم افتراضية
        if "enabled" not in settings:
            settings["enabled"] = False
        if "interval_seconds" not in settings:
            settings["interval_seconds"] = 3600
        if "last_index" not in settings:
            settings["last_index"] = 0
        return settings

async def update_setting(pool: Pool, key: str, value: Any):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO engagement_settings (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = $2",
            key, json.dumps(value)
        )

async def toggle_engagement(pool: Pool) -> bool:
    settings = await get_engagement_settings(pool)
    new_state = not settings.get("enabled", False)
    await update_setting(pool, "enabled", new_state)
    return new_state

# عمليات السجل (Messages CRUD)
async def add_engagement_message(pool: Pool, text: str, buttons: Optional[List[Dict]] = None) -> int:
    async with pool.acquire() as conn:
        buttons_json = json.dumps(buttons) if buttons else None
        return await conn.fetchval(
            "INSERT INTO engagement_messages (text, buttons) VALUES ($1, $2) RETURNING id",
            text, buttons_json
        )

async def get_all_messages(pool: Pool) -> List[Dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM engagement_messages ORDER BY id ASC")
        return [dict(row) for row in rows]

async def get_active_messages(pool: Pool) -> List[Dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM engagement_messages WHERE is_active = TRUE ORDER BY id ASC")
        return [dict(row) for row in rows]

async def get_message_by_id(pool: Pool, msg_id: int) -> Optional[Dict[str, Any]]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM engagement_messages WHERE id = $1", msg_id)
        return dict(row) if row else None

async def update_message_text(pool: Pool, msg_id: int, new_text: str):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE engagement_messages SET text = $1 WHERE id = $2", new_text, msg_id)

async def toggle_message_status(pool: Pool, msg_id: int) -> bool:
    async with pool.acquire() as conn:
        current = await conn.fetchval("SELECT is_active FROM engagement_messages WHERE id = $1", msg_id)
        new_state = not current
        await conn.execute("UPDATE engagement_messages SET is_active = $1 WHERE id = $2", new_state, msg_id)
        return new_state

async def delete_message(pool: Pool, msg_id: int):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM engagement_messages WHERE id = $1", msg_id)
