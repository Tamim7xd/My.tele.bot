"""
نصوص "🎮 الألعاب" في لوحة التحكم.
"""


def games_main_text(cooldown: int) -> str:
    return (
        f"🎮 <b>الألعاب</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⏱️ فترة الانتظار بين الألعاب: {cooldown} ثانية\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط ✅/❌ لتفعيل/تعطيل لعبة، أو ⚙️ لإعداداتها:"
    )


COOLDOWN_PROMPT = "✏️ أرسل فترة الانتظار الجديدة بين فتح الألعاب (بالثواني)."

INVALID_NUMBER = "❌ يجب إرسال رقم صحيح موجب."


def cooldown_updated_text(seconds: int) -> str:
    return f"✅ تم تحديث فترة الانتظار إلى: {seconds} ثانية"


# ===== أسئلة مرحة / الألغاز =====

def questions_settings_text(game_label: str, questions: list[dict], timeout: int) -> str:
    return (
        f"{game_label}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📋 عدد الأسئلة: {len(questions)}\n"
        f"⏱️ مهلة الإجابة: {timeout} ثانية\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط 🗑️ للحذف، أو ➕ للإضافة:"
    )


QUESTION_PROMPT = "✏️ أرسل نص السؤال."

ANSWERS_PROMPT = (
    "✏️ أرسل الإجابات المقبولة مفصولة بفواصل (,).\n"
    "مثال: جوعان,متخبل من الجوع,اموت"
)

REWARD_PROMPT = "💰 أرسل قيمة المكافأة (رقم، يدعم صيغة 1.000)."

TIMEOUT_PROMPT = "⏱️ أرسل مهلة الإجابة الجديدة بالثواني."


def question_added_text(question: str) -> str:
    return f"✅ تمت إضافة السؤال:\n«{question}»"


def question_removed_text() -> str:
    return "🗑️ تم حذف السؤال."


def timeout_updated_text(seconds: int) -> str:
    return f"✅ تم تحديث المهلة إلى: {seconds} ثانية"


# ===== حجر ورقة مقص =====

def rps_settings_text(reward: int) -> str:
    return f"🪨📄✂️ <b>حجر ورقة مقص</b>\n━━━━━━━━━━━━━━━\n🎁 المكافأة: {reward:,} د.ع"


def rps_reward_updated_text(reward: int) -> str:
    return f"✅ تم تحديث المكافأة إلى: {reward:,} د.ع"


# ===== صندوق الحظ =====

def lucky_box_settings_text(fee: int) -> str:
    return f"📦 <b>صندوق الحظ</b>\n━━━━━━━━━━━━━━━\n💰 رسوم الدخول: {fee:,} د.ع\n━━━━━━━━━━━━━━━\nالنتائج المتاحة:"


LUCKY_BOX_FEE_PROMPT = "✏️ أرسل رسوم الدخول الجديدة (يدعم صيغة 1.000)."

LUCKY_BOX_AMOUNT_PROMPT = "💰 أرسل مبلغ النتيجة الجديدة (يدعم صيغة 1.000)."

LUCKY_BOX_WEIGHT_PROMPT = "📊 أرسل نسبة احتمالية ظهور هذه النتيجة (رقم من 1 إلى 100)."


def lucky_box_fee_updated_text(fee: int) -> str:
    return f"✅ تم تحديث رسوم الدخول إلى: {fee:,} د.ع"


def lucky_box_outcome_added_text(amount: int, weight: int) -> str:
    return f"✅ تمت إضافة نتيجة: {amount:,} د.ع بنسبة {weight}%"


LUCKY_BOX_OUTCOME_REMOVED = "🗑️ تم حذف النتيجة."

LUCKY_BOX_MIN_OUTCOME = "❌ يجب أن تبقى نتيجة واحدة على الأقل."


# ===== الناجي الأخير =====

def last_survivor_settings_text(fee: int, join_window: int, min_players: int, elimination_delay: int) -> str:
    return (
        f"🧟 <b>الناجي الأخير</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 رسوم الدخول: {fee:,} د.ع\n"
        f"⏳ نافذة الانضمام: {join_window} ثانية\n"
        f"👥 الحد الأدنى للاعبين: {min_players}\n"
        f"⚡ سرعة الحذف: {elimination_delay} ثانية بين كل اسم\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر ما تريد تعديله:"
    )


LS_FEE_PROMPT = "✏️ أرسل رسوم الدخول الجديدة (يدعم صيغة 1.000)."

LS_JOIN_WINDOW_PROMPT = "✏️ أرسل مدة نافذة الانضمام الجديدة بالثواني."

LS_MIN_PLAYERS_PROMPT = "✏️ أرسل الحد الأدنى الجديد لعدد اللاعبين."

LS_ELIMINATION_DELAY_PROMPT = "✏️ أرسل سرعة الحذف الجديدة بالثواني (التأخير بين كل اسم يخرج)."


def ls_updated_text(fee: int, join_window: int, min_players: int, elimination_delay: int) -> str:
    return (
        f"✅ تم التحديث:\n"
        f"💰 الرسوم: {fee:,} د.ع | ⏳ النافذة: {join_window}ث | "
        f"👥 الحد الأدنى: {min_players} | ⚡ السرعة: {elimination_delay}ث"
    )
