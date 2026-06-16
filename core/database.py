"""
الاتصال بقاعدة بيانات PostgreSQL وإنشاء الجداول الأساسية.
"""

import asyncpg
from core.config import DATABASE_URL

db_pool: asyncpg.Pool | None = None

# ═══════════════════════════════════════
# الصلاحيات الافتراضية
# ═══════════════════════════════════════
DEFAULT_PERMISSIONS = [
    ("ban", "🚫 حظر عضو", "حظر عضو من المجموعة", "moderation", "🚫"),
    ("unban", "✅ فك الحظر", "فك حظر عن عضو", "moderation", "✅"),
    ("mute", "🔇 كتم عضو", "كتم عضو مؤقتاً", "moderation", "🔇"),
    ("unmute", "🔊 فك الكتم", "فك كتم عن عضو", "moderation", "🔊"),
    ("warn", "⚠️ تحذير", "إعطاء تحذير لعضو", "moderation", "⚠️"),
    ("kick", "👢 طرد", "طرد عضو من المجموعة", "moderation", "👢"),
    ("cleanup", "🧹 تنظيف", "تنظيف وحذف الرسائل", "systems", "🧹"),
    ("protection", "🛡️ الحماية", "إدارة إعدادات الحماية", "systems", "🛡️"),
    ("announcements", "📢 إعلانات", "إرسال إعلانات للمجموعة", "systems", "📢"),
    ("moderation", "⚖️ الإشراف", "إدارة الإشراف والعقوبات", "systems", "⚖️"),
    ("manage_settings", "⚙️ إعدادات", "تعديل إعدادات البوت", "admin", "⚙️"),
    ("manage_ranks", "👑 العضويات", "إضافة/تعديل العضويات", "admin", "👑"),
    ("manage_staff", "👥 الطاقم", "ترقية/تنزيل المشرفين", "admin", "👥"),
    ("view_logs", "📋 السجلات", "مشاهدة سجل الأرشيف", "admin", "📋"),
    ("view_stats", "📊 الإحصائيات", "مشاهدة إحصائيات المجموعة", "admin", "📊"),
    ("give_points", "💰 إعطاء نقاط", "إضافة رصيد لعضو", "economy", "💰"),
    ("take_points", "💸 خصم نقاط", "خصم رصيد من عضو", "economy", "💸"),
    ("manage_rewards", "🎁 المكافآت", "إنشاء/تعديل المكافآت", "economy", "🎁"),
    ("wallet", "💳 المحفظة", "الوصول لنظام المحفظة", "economy", "💳"),
    ("leaderboard", "🏆 المتصدرين", "عرض لوحة المتصدرين", "economy", "🏆"),
    ("pin_messages", "📌 تثبيت", "تثبيت/فك تثبيت رسائل", "content", "📌"),
    ("delete_messages", "🗑️ حذف", "حذف رسائل الأعضاء", "content", "🗑️"),
    ("edit_messages", "✏️ تعديل", "تعديل رسائل البوت", "content", "✏️"),
    ("bypass_protection", "🔓 تجاوز", "تجاوز قوانين الحماية", "special", "🔓"),
    ("use_ai", "🤖 الذكاء", "استخدام Gemini AI", "special", "🤖"),
    ("owner_panel", "🔐 لوحة المالك", "الوصول الكامل للوحة التحكم", "special", "🔐"),
]

# ═══════════════════════════════════════
# العضويات الافتراضية
# ═══════════════════════════════════════
DEFAULT_RANKS = [
    (1, 'owner', '👑 المالك', 1, '#FFD700', '["*"]', True, 0),
    (2, 'admin', '🔥 الأدمن', 2, '#FF4444', '["ban","unban","mute","unmute","warn","kick","cleanup","protection","announcements","moderation","manage_settings","manage_staff","view_logs","view_stats","give_points","take_points","manage_rewards","wallet","leaderboard","pin_messages","delete_messages","edit_messages","bypass_protection","use_ai"]', True, 0),
    (3, 'moderator', '⚡ المشرف', 3, '#4488FF', '["mute","unmute","warn","kick","cleanup","delete_messages","view_stats","leaderboard"]', True, 0),
    (4, 'member', '👤 العضو', 4, '#888888', '[]', True, 0),
]


async def connect_db() -> asyncpg.Pool:
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=DATABASE_URL)
    await create_tables()
    await init_permissions()
    await init_default_ranks()
    return db_pool


async def create_tables() -> None:
    assert db_pool is not None

    async with db_pool.acquire() as conn:
        # ─── جدول العضويات ───
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ranks (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                level INTEGER NOT NULL UNIQUE,
                color TEXT DEFAULT '#FFFFFF',
                icon TEXT DEFAULT '👤',
                permissions JSONB DEFAULT '[]',
                is_protected BOOLEAN DEFAULT FALSE,
                created_by INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # ─── جدول الصلاحيات ───
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS permissions_list (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'general',
                icon TEXT DEFAULT '⚡'
            );
        """)

        # ─── جدول الأعضاء (محدّث) ───
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS members (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance BIGINT DEFAULT 0,
                level INTEGER DEFAULT 1,
                rank_id INTEGER REFERENCES ranks(id) DEFAULT 4,
                messages_count INTEGER DEFAULT 0,
                permissions JSONB DEFAULT '{}',
                protection_exceptions JSONB DEFAULT '{}',
                is_banned BOOLEAN DEFAULT FALSE,
                is_muted BOOLEAN DEFAULT FALSE,
                muted_until TIMESTAMP,
                banned_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # ─── جدول الأرشيف ───
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS archive (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES members(user_id),
                action_type TEXT NOT NULL,
                amount BIGINT,
                reason TEXT,
                replied_message TEXT,
                done_by BIGINT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # ─── جدول سجل الحماية ───
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS protection_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES members(user_id),
                violation_type TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # ─── جدول الإعدادات ───
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value JSONB NOT NULL
            );
        """)

        # ─── ترقية الجداول القديمة ───
        await conn.execute("""
            ALTER TABLE members ADD COLUMN IF NOT EXISTS rank_id INTEGER REFERENCES ranks(id) DEFAULT 4
        """)
        await conn.execute("""
            ALTER TABLE members DROP COLUMN IF EXISTS rank
        """)


async def init_permissions() -> None:
    """إنشاء قائمة الصلاحيات الافتراضية"""
    assert db_pool is not None
    async with db_pool.acquire() as conn:
        for perm in DEFAULT_PERMISSIONS:
            await conn.execute("""
                INSERT INTO permissions_list (code, display_name, description, category, icon)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (code) DO NOTHING
            """, perm[0], perm[1], perm[2], perm[3], perm[4])


async def init_default_ranks() -> None:
    """إنشاء العضويات الافتراضية"""
    assert db_pool is not None
    async with db_pool.acquire() as conn:
        for rank in DEFAULT_RANKS:
            await conn.execute("""
                INSERT INTO ranks (id, name, display_name, level, color, permissions, is_protected, created_by)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8)
                ON CONFLICT (id) DO NOTHING
            """, *rank)


# ═══════════════════════════════════════
# دوال العضويات
# ═══════════════════════════════════════

async def get_ranks(pool: asyncpg.Pool) -> list:
    rows = await pool.fetch("SELECT * FROM ranks ORDER BY level ASC")
    return [dict(row) for row in rows]


async def get_rank_by_id(pool: asyncpg.Pool, rank_id: int) -> dict | None:
    row = await pool.fetchrow("SELECT * FROM ranks WHERE id = $1", rank_id)
    return dict(row) if row else None


async def get_rank_by_name(pool: asyncpg.Pool, name: str) -> dict | None:
    row = await pool.fetchrow("SELECT * FROM ranks WHERE name = $1", name)
    return dict(row) if row else None


async def add_rank(pool: asyncpg.Pool, name: str, display_name: str, level: int,
                   color: str, icon: str, permissions: list, created_by: int = 0) -> int:
    row = await pool.fetchrow("""
        INSERT INTO ranks (name, display_name, level, color, icon, permissions, created_by)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
        RETURNING id
    """, name, display_name, level, color, icon, permissions, created_by)
    return row['id']


async def update_rank(pool: asyncpg.Pool, rank_id: int, **kwargs) -> None:
    allowed = ['display_name', 'color', 'icon', 'permissions']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
    values = list(updates.values())
    await pool.execute(f"""
        UPDATE ranks SET {set_clause} WHERE id = $1 AND is_protected = FALSE
    """, rank_id, *values)


async def delete_rank(pool: asyncpg.Pool, rank_id: int) -> bool:
    result = await pool.execute("""
        DELETE FROM ranks WHERE id = $1 AND is_protected = FALSE
    """, rank_id)
    return "DELETE 1" in result


async def get_rank_permissions(pool: asyncpg.Pool, rank_id: int) -> list:
    row = await pool.fetchrow("SELECT permissions FROM ranks WHERE id = $1", rank_id)
    if row and row['permissions']:
        return row['permissions'] if isinstance(row['permissions'], list) else []
    return []


async def set_rank_permissions(pool: asyncpg.Pool, rank_id: int, permissions: list) -> None:
    await pool.execute("""
        UPDATE ranks SET permissions = $1::jsonb WHERE id = $2
    """, permissions, rank_id)


async def get_permissions_list(pool: asyncpg.Pool, category: str = None) -> list:
    if category:
        rows = await pool.fetch("SELECT * FROM permissions_list WHERE category = $1 ORDER BY display_name", category)
    else:
        rows = await pool.fetch("SELECT * FROM permissions_list ORDER BY category, display_name")
    return [dict(row) for row in rows]


async def get_permission_by_code(pool: asyncpg.Pool, code: str) -> dict | None:
    row = await pool.fetchrow("SELECT * FROM permissions_list WHERE code = $1", code)
    return dict(row) if row else None


async def has_permission(pool: asyncpg.Pool, user_id: int, permission: str) -> bool:
    member = await pool.fetchrow("""
        SELECT r.permissions FROM members m
        JOIN ranks r ON m.rank_id = r.id
        WHERE m.user_id = $1
    """, user_id)
    if not member:
        return False
    perms = member['permissions'] or []
    if "*" in perms:
        return True
    return permission in perms


async def get_user_rank(pool: asyncpg.Pool, user_id: int) -> dict | None:
    row = await pool.fetchrow("""
        SELECT r.* FROM members m
        JOIN ranks r ON m.rank_id = r.id
        WHERE m.user_id = $1
    """, user_id)
    return dict(row) if row else None


async def set_user_rank(pool: asyncpg.Pool, user_id: int, rank_id: int, promoted_by: int = None) -> None:
    await pool.execute("""
        UPDATE members SET rank_id = $1 WHERE user_id = $2
    """, rank_id, user_id)
    await pool.execute("""
        INSERT INTO archive (user_id, action_type, reason, done_by)
        VALUES ($1, 'rank_change', $2, $3)
    """, user_id, f"تغيير عضوية إلى {rank_id}", promoted_by)


# ═══════════════════════════════════════
# دوال الإعدادات
# ═══════════════════════════════════════

async def get_setting(pool: asyncpg.Pool, key: str, default=None):
    import json
    row = await pool.fetchrow("SELECT value FROM settings WHERE key = $1", key)
    if row is None:
        return default
    return row['value']


async def set_setting(pool: asyncpg.Pool, key: str, value) -> None:
    import json
    await pool.execute("""
        INSERT INTO settings (key, value) VALUES ($1, $2::jsonb)
        ON CONFLICT (key) DO UPDATE SET value = $2::jsonb
    """, key, json.dumps(value))


async def get_pool() -> asyncpg.Pool:
    assert db_pool is not None, "لم يتم الاتصال بقاعدة البيانات"
    return db_pool


async def close_db() -> None:
    if db_pool is not None:
        await db_pool.close()
