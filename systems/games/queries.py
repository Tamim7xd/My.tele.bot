"""
نظام الألعاب (games) - الإعدادات المشتركة وأدوات عامة.

كل لعبة لها إعداداتها الخاصة المخزَّنة في جدول settings (key مستقل
لكل لعبة)، بالإضافة لإعداد عام واحد لفترة الانتظار بين الألعاب
(cooldown) يُطبَّق على كل الألعاب معاً.
"""

import asyncpg

from core.database import get_setting, set_setting


GAMES_COOLDOWN_KEY = "games_cooldown_seconds"
DEFAULT_GAMES_COOLDOWN = 10

GAME_SELECTION_TIMEOUT = 3  # ثوانٍ لاختيار اللعبة من القائمة


async def get_games_cooldown(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, GAMES_COOLDOWN_KEY, DEFAULT_GAMES_COOLDOWN)


async def set_games_cooldown(pool: asyncpg.Pool, seconds: int) -> None:
    await set_setting(pool, GAMES_COOLDOWN_KEY, seconds)


# ===== تفعيل/تعطيل كل لعبة =====

GAMES_ENABLED_KEY = "games_enabled"

ALL_GAMES = ["trivia", "rps", "lucky_box", "riddles", "last_survivor"]

GAME_LABELS = {
    "trivia": "🧠 أسئلة مرحة",
    "rps": "🪨📄✂️ حجر ورقة مقص",
    "lucky_box": "📦 صندوق الحظ",
    "riddles": "🧩 الألغاز",
    "last_survivor": "🧟 الناجي الأخير",
}

DEFAULT_ENABLED = {game: True for game in ALL_GAMES}


async def get_enabled_games(pool: asyncpg.Pool) -> dict:
    stored = await get_setting(pool, GAMES_ENABLED_KEY, None)

    merged = dict(DEFAULT_ENABLED)
    if isinstance(stored, dict):
        merged.update(stored)

    return merged


async def is_game_enabled(pool: asyncpg.Pool, game_key: str) -> bool:
    enabled = await get_enabled_games(pool)
    return enabled.get(game_key, True)


async def toggle_game_enabled(pool: asyncpg.Pool, game_key: str) -> bool:
    enabled = await get_enabled_games(pool)
    enabled[game_key] = not enabled.get(game_key, True)
    await set_setting(pool, GAMES_ENABLED_KEY, enabled)
    return enabled[game_key]
