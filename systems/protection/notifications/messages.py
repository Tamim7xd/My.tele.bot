"""
نصوص نظام الحماية (protection).
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


VIOLATION_REPLY = "🚫 لا تتجاوز القوانين"


VIOLATION_LABELS = {
    "links": "🔗 رابط",
    "files": "📎 ملف",
    "videos": "🎥 فيديو",
    "voice": "🎙️ بصمة صوتية",
    "location": "📍 موقع",
    "photos": "🖼️ صورة",
    "stickers_gifs": "🎞️ ملصق/GIF",
    "bad_words": "🤬 كلام مسيء",
}


# ===== لوحة الإعدادات العامة =====

def settings_text(settings: dict) -> str:
    from systems.protection.queries import FEATURE_KEYS, FEATURE_LABELS

    lines = ["🛡️ <b>إعدادات الحماية</b>", "━━━━━━━━━━━━━━━"]

    for key in FEATURE_KEYS:
        status = "✅ مسموح" if settings.get(key) else "❌ محظور"
        lines.append(f"{FEATURE_LABELS[key]}: {status}")

    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"📝 الكلمات المحظورة: {len(settings.get('banned_words', []))}")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("اضغط لتبديل أي ميزة:")

    return "\n".join(lines)


# ===== الكلمات المحظورة =====

def banned_words_text(words: list[str]) -> str:
    if not words:
        return "📝 <b>الكلمات المحظورة</b>\n━━━━━━━━━━━━━━━\nلا يوجد كلمات محظورة حالياً."

    lines = [f"📝 <b>الكلمات المحظورة</b> ({len(words)})", "━━━━━━━━━━━━━━━"]
    lines.append("اضغط 🗑️ للحذف، أو ➕ للإضافة:")

    return "\n".join(lines)


ADD_WORD_PROMPT = "✏️ أرسل الكلمة المراد حظرها."

ADD_WORD_DUPLICATE = "❌ هذه الكلمة موجودة بالفعل في القائمة."


def word_added_text(word: str) -> str:
    return f"✅ تمت إضافة \"{word}\" لقائمة الكلمات المحظورة."


def word_removed_text(word: str) -> str:
    return f"🗑️ تم حذف \"{word}\" من قائمة الكلمات المحظورة."


# ===== لوحة المحذوفات =====

def deleted_main_text(violators_count: int) -> str:
    return (
        f"🗑️ <b>لوحة المحذوفات</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 عدد الأعضاء: {violators_count}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط لعرض القائمة:"
    )


def deleted_list_text(total: int) -> str:
    if total == 0:
        return "🗑️ <b>قائمة المحذوفات</b>\n━━━━━━━━━━━━━━━\nلا يوجد محذوفات حالياً. 🎉"

    return f"🗑️ <b>قائمة المحذوفات</b> ({total})\n━━━━━━━━━━━━━━━\nاختر عضواً:"


def member_deleted_text(full_name: str, entries: list, total: int) -> str:
    if not entries:
        return f"🗑️ <b>محذوفات {full_name}</b>\n━━━━━━━━━━━━━━━\nلا يوجد محذوفات."

    lines = [f"🗑️ <b>محذوفات {full_name}</b> ({total})", "━━━━━━━━━━━━━━━"]

    for entry in entries:
        label = VIOLATION_LABELS.get(entry["violation_type"], entry["violation_type"])
        content = entry["content"] or "(بدون محتوى نصي)"
        date_str = entry["created_at"].strftime("%Y-%m-%d %H:%M")

        lines.append(label)
        lines.append(f"📝 المحتوى: {content}")
        lines.append(f"🕒 {date_str}")
        lines.append("───────────────")

    if lines and lines[-1] == "───────────────":
        lines.pop()

    return "\n".join(lines)


# ===== الإجراءات من لوحة المحذوفات =====

WARN_SUCCESS = "⚠️ تم تحذير العضو."

MUTE_SUCCESS = "🔇 تم كتم العضو لمدة 10 دقائق."


# ===== استثناءات فردية لعضو =====

def member_exceptions_text(full_name: str) -> str:
    return (
        f"🛡️ <b>استثناءات الحماية - {full_name}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ = مسموح له بتجاوز الحظر العام لهذه الميزة\n"
        f"❌ = يخضع للإعداد العام\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط لتبديل أي ميزة:"
    )
