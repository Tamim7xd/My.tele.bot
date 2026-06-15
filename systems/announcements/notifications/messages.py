"""
نصوص نظام الإعلانات (announcements).
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


# ===== لوحة التحكم =====

def list_text(announcements: list[dict]) -> str:
    if not announcements:
        return "📢 <b>الإعلانات</b>\n━━━━━━━━━━━━━━━\nلا يوجد إعلانات حالياً.\nاضغط ➕ لإضافة إعلان جديد."

    lines = [f"📢 <b>الإعلانات</b> ({len(announcements)})", "━━━━━━━━━━━━━━━"]

    for ann in announcements:
        delete_after = ann.get("delete_after", 0)
        delete_label = "بلا حذف" if delete_after == 0 else f"حذف بعد {delete_after} ثانية"
        lines.append(f"• \"{ann['trigger']}\" — {delete_label}")

    lines.append("━━━━━━━━━━━━━━━")
    lines.append("اختر إعلاناً لتعديله، أو ➕ لإضافة جديد:")

    return "\n".join(lines)


def announcement_details_text(ann: dict) -> str:
    delete_after = ann.get("delete_after", 0)
    delete_label = "بلا حذف" if delete_after == 0 else f"حذف بعد {delete_after} ثانية"

    text_preview = ann.get("text") or "(بدون نص)"

    return (
        f"📢 <b>الأمر: {ann['trigger']}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 النص:\n{text_preview}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⏱️ {delete_label}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر إجراءً:"
    )


# ===== إضافة إعلان (FSM) =====

ADD_TRIGGER_PROMPT = "✏️ أرسل الأمر الذي سيشغّل الإعلان (كلمة واحدة، بدون \"/\").\nمثال: قوانين"

ADD_TRIGGER_INVALID = "❌ يجب إرسال كلمة واحدة فقط بدون مسافات أو \"/\"."

ADD_TRIGGER_DUPLICATE = "❌ هذا الأمر مستخدم بالفعل لإعلان آخر. أرسل أمراً آخر."

ADD_TEXT_PROMPT = "📝 أرسل نص الإعلان، أو أرسل \"تخطي\" لتركه بدون نص."

SKIP_WORD = "تخطي"


def add_success_text(ann: dict) -> str:
    return "✅ تم إضافة الإعلان بنجاح!\n\n" + announcement_details_text(ann)


# ===== تعديل/حذف =====

DELETE_CONFIRM_TEXT = "⚠️ هل تريد حذف هذا الإعلان نهائياً؟"

DELETE_SUCCESS = "🗑️ تم حذف الإعلان."

EDIT_TEXT_PROMPT = "📝 أرسل النص الجديد للإعلان، أو أرسل \"تخطي\" لإزالة النص الحالي."


def edit_success_text(ann: dict) -> str:
    return "✅ تم التحديث!\n\n" + announcement_details_text(ann)


# ===== مدة الحذف =====

DELETE_AFTER_PROMPT = "⏱️ اختر مدة حذف رسالة الإعلان تلقائياً بعد إرسالها:"


def delete_after_updated_text(ann: dict) -> str:
    return "✅ تم التحديث!\n\n" + announcement_details_text(ann)


# ===== التشغيل في المجموعة =====

CANCELLED = "❌ تم الإلغاء."
