"""
لوحة مفاتيح قائمة الألعاب الرئيسية.

كل زر مقيَّد بـ owner_id (صاحب رسالة "لعبة") - أي عضو آخر يضغط
لا يحدث له شيء (يُتجاهل في الهاندلر نفسه عبر فحص from_user.id).
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from systems.games.queries import GAME_LABELS


def games_menu_keyboard(owner_id: int, enabled_games: dict) -> InlineKeyboardMarkup:
    """قائمة الألعاب المتاحة (المُفعَّلة فقط من اللوحة)."""
    buttons = []

    for game_key, label in GAME_LABELS.items():
        if not enabled_games.get(game_key, True):
            continue

        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"games:open:{game_key}:{owner_id}")
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
