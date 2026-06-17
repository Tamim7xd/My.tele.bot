"""
لوحات المفاتيح (Inline Keyboards) لـ "🎮 الألعاب" في لوحة التحكم.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from systems.games.queries import GAME_LABELS


def games_main_keyboard(enabled_games: dict) -> InlineKeyboardMarkup:
    """القائمة الرئيسية لإدارة الألعاب: تفعيل/تعطيل كل لعبة + إعدادات."""
    buttons = []

    for game_key, label in GAME_LABELS.items():
        status_icon = "✅" if enabled_games.get(game_key, True) else "❌"
        buttons.append([
            InlineKeyboardButton(text=f"{status_icon} {label}", callback_data=f"owner:game_toggle:{game_key}"),
            InlineKeyboardButton(text="⚙️ إعدادات", callback_data=f"owner:game_settings:{game_key}"),
        ])

    buttons.append([InlineKeyboardButton(text="⏱️ فترة الانتظار العامة", callback_data="owner:games_cooldown")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_games_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:games")],
        ]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:games")],
        ]
    )


# ===== أسئلة مرحة / الألغاز (قائمة عناصر + إضافة) =====

def questions_list_keyboard(questions: list[dict], game_key: str, back_callback: str) -> InlineKeyboardMarkup:
    """قائمة الأسئلة/الألغاز: كل عنصر مع 🗑️ حذف + ➕ إضافة + ✏️ تعديل المهلة."""
    buttons = []

    for i, q in enumerate(questions):
        short_question = q["question"][:30] + ("..." if len(q["question"]) > 30 else "")
        buttons.append([
            InlineKeyboardButton(text=f"❓ {short_question}", callback_data="owner:noop"),
            InlineKeyboardButton(text="🗑️", callback_data=f"owner:{game_key}_remove:{i}"),
        ])

    buttons.append([InlineKeyboardButton(text="➕ إضافة سؤال", callback_data=f"owner:{game_key}_add")])
    buttons.append([InlineKeyboardButton(text="⏱️ تعديل المهلة", callback_data=f"owner:{game_key}_timeout")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=back_callback)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== صندوق الحظ =====

def lucky_box_settings_keyboard(outcomes: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="💰 تعديل رسوم الدخول", callback_data="owner:lucky_box_fee")],
    ]

    for i, outcome in enumerate(outcomes):
        buttons.append([
            InlineKeyboardButton(
                text=f"💵 {outcome['amount']:,} (نسبة {outcome['weight']}%)",
                callback_data="owner:noop",
            ),
            InlineKeyboardButton(text="🗑️", callback_data=f"owner:lucky_box_remove:{i}"),
        ])

    buttons.append([InlineKeyboardButton(text="➕ إضافة نتيجة", callback_data="owner:lucky_box_add")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:games")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== الناجي الأخير =====

def last_survivor_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 رسوم الدخول", callback_data="owner:ls_fee")],
            [InlineKeyboardButton(text="⏳ نافذة الانضمام", callback_data="owner:ls_join_window")],
            [InlineKeyboardButton(text="👥 الحد الأدنى للاعبين", callback_data="owner:ls_min_players")],
            [InlineKeyboardButton(text="⚡ سرعة الحذف", callback_data="owner:ls_elimination_delay")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:games")],
        ]
    )


# ===== حجر ورقة مقص =====

def rps_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎁 تعديل المكافأة", callback_data="owner:rps_reward")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:games")],
        ]
    )
