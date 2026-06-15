"""
نصوص نظام الحماية (protection).
تعديل أي نص هنا لا يؤثر على أي نظام آخر.

تم التعديل: إضافة نصوص لجهات الاتصال والاستثناءات.
"""


# ===== الرسائل التحذيرية =====

VIOLATION_REPLY = "🚫 لا تتجاوز القوانين"

VIOLATION_REPLY_CONTACT = "🚫 لا يُسمح بمشاركة جهات الاتصال"

VIOLATION_REPLY_LOCATION = "🚫 لا يُسمح بمشاركة الموقع الجغرافي"


# ===== تسميات أنواع المخالفات =====

VIOLATION_LABELS = {
    "links": "🔗 رابط",
    "files": "📎 ملف",
    "videos": "🎥 فيديو",
    "voice": "🎙️ بصمة صوتية",
    "location": "📍 موقع",
    "photos": "🖼️ صورة",
    "stickers_gifs": "🎞️ ملصق/GIF",
    "bad_words": "🤬 كلام مسيء",
    "contacts": "📇 جهة اتصال",  # جديد
}


# ===== لوحة الإعدادات العامة =====

def settings_text(settings: dict) -> str:
    from systems.protection.queries import FEATURE_KEYS, FEATURE_LABELS

    lines = ["🛡️ <b>إعدادات الحماية</b>", "━━━━━━━━━━━━━━━"]

    for key in FEATURE_KEYS:
        status = "✅ محظور" if settings.get(key) else "❌ مسموح"
        lines.append(f"{FEATURE_LABELS[key]}: {status}")

    lines.append("━━━━━━━━━━━━━━━")
    
    banned_words = settings.get('banned_words', [])
    lines.append(f"📝 الكلمات المحظورة: {len(banned_words)}")
    
    if banned_words:
        # عرض أول 5 كلمات كمعاينة
        preview = "، ".join(banned_words[:5])
        if len(banned_words) > 5:
            preview += f" +{len(banned_words) - 5}"
        lines.append(f"   ({preview})")
    
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("اضغط لتبديل أي ميزة:")

    return "\n".join(lines)


# ===== الكلمات المحظورة =====

def banned_words_text(words: list[str]) -> str:
    if not words:
        return "📝 <b>الكلمات المحظورة</b>\n━━━━━━━━━━━━━━━\nلا يوجد كلمات محظورة حالياً.\n\nيمكنك إضافة كلمات جديدة بالضغط على زر الإضافة."

    lines = [f"📝 <b>الكلمات المحظورة</b> ({len(words)})", "━━━━━━━━━━━━━━━"]
    lines.append("اضغط 🗑️ للحذف، أو ➕ للإضافة:")
    lines.append("")
    
    # عرض أول 10 كلمات كمعاينة
    for i, word in enumerate(words[:10], 1):
        lines.append(f"{i}. {word}")
    
    if len(words) > 10:
        lines.append(f"... و {len(words) - 10} كلمات أخرى")

    return "\n".join(lines)


ADD_WORD_PROMPT = "✏️ أرسل الكلمة المراد حظرها.\n\nملاحظة: سيتم تطبيع الكلمة تلقائياً، لذا يمكنك كتابتها بالشكل المعتاد."

ADD_WORD_DUPLICATE = "❌ هذه الكلمة موجودة بالفعل في القائمة."


def word_added_text(word: str) -> str:
    return f"✅ تمت إضافة \"{word}\" لقائمة الكلمات المحظورة.\n\nسيتم حظرها حتى مع التلاعب (تشكيل، عربيزي، تكرار)."


def word_removed_text(word: str) -> str:
    return f"🗑️ تم حذف \"{word}\" من قائمة الكلمات المحظورة."


# ===== لوحة المحذوفات =====

def deleted_main_text(violators_count: int) -> str:
    if violators_count == 0:
        return (
            f"🗑️ <b>لوحة المحذوفات</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✨ لا يوجد أي عضو مخالف حالياً.\n"
            f"━━━━━━━━━━━━━━━\n"
            f"النظام يعمل بشكل طبيعي."
        )
    
    return (
        f"🗑️ <b>لوحة المحذوفات</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 عدد الأعضاء المخالفين: {violators_count}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط لعرض القائمة:"
    )


def deleted_list_text(total: int) -> str:
    if total == 0:
        return "🗑️ <b>قائمة المحذوفات</b>\n━━━━━━━━━━━━━━━\nلا يوجد محذوفات حالياً. 🎉"

    return f"🗑️ <b>قائمة المخالفين</b> ({total})\n━━━━━━━━━━━━━━━\nاختر عضواً لعرض محذوفاته:"


def member_deleted_text(full_name: str, entries: list, total: int) -> str:
    if not entries:
        return f"🗑️ <b>محذوفات {full_name}</b>\n━━━━━━━━━━━━━━━\nلا يوجد محذوفات لهذا العضو."

    lines = [f"🗑️ <b>محذوفات {full_name}</b> ({total})", "━━━━━━━━━━━━━━━"]

    for i, entry in enumerate(entries, 1):
        violation_type = entry.get("violation_type") or entry.get("violation_type")
        label = VIOLATION_LABELS.get(violation_type, violation_type)
        content = entry.get("content") or "(بدون محتوى نصي)"
        
        # تنسيق التاريخ
        created_at = entry.get("created_at")
        if created_at:
            date_str = created_at.strftime("%Y-%m-%d %H:%M")
        else:
            date_str = "تاريخ غير معروف"
        
        lines.append(f"<b>{i}. {label}</b>")
        lines.append(f"📝 {content[:150]}")
        lines.append(f"🕒 {date_str}")
        
        if i < len(entries):
            lines.append("───────────────")

    return "\n".join(lines)


# ===== الإجراءات من لوحة المحذوفات =====

WARN_SUCCESS = "⚠️ تم تحذير العضو بنجاح."

MUTE_SUCCESS = "🔇 تم كتم العضو لمدة 10 دقائق."


# ===== استثناءات فردية لعضو (جديد - محسن) =====

def member_exceptions_text(full_name: str) -> str:
    return (
        f"🛡️ <b>استثناءات الحماية - {full_name}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ <b>مسموح له بتجاوز الحظر العام</b> لهذه الميزة\n"
        f"❌ <b>يخضع للإعداد العام</b> (محظور إذا كان مفعلاً)\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📌 ملاحظة: الاستثناءات تطغى على الإعدادات العامة.\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط لتبديل أي ميزة:"
    )


def member_exception_toggled_text(full_name: str, feature_label: str, is_exempt: bool) -> str:
    """
    رسالة تأكيد بعد تغيير استثناء عضو.
    """
    if is_exempt:
        return f"✅ تم استثناء {full_name} من حظر {feature_label}\n\nأصبح بإمكانه نشر {feature_label} حتى لو كان محظوراً عاماً."
    else:
        return f"❌ تم إلغاء استثناء {full_name} من حظر {feature_label}\n\nأصبح يخضع للإعدادات العامة لـ {feature_label}."


# ===== رسائل مساعدة =====

HELP_TEXT = """
🛡️ <b>نظام الحماية</b>

<b>ما الذي يحظره البوت؟</b>
• 🔗 الروابط
• 📎 الملفات
• 🎥 الفيديو
• 🎙️ البصمات الصوتية
• 📍 الموقع الجغرافي
• 🖼️ الصور (يمكن تفعيلها)
• 🎞️ الملصقات و GIF
• 🤬 الكلمات المسيئة
• 📇 جهات الاتصال

<b>كيف يعمل التطبيع؟</b>
يكتشف الكلمات المحظورة حتى مع التلاعب:
• التشكيل (حَرَام)
• العربيزي (7رام)
• التكرار (حححرام)
• التقسيم (ح ر ا م)

<b>الاستثناءات الفردية</b>
يمكن استثناء أعضاء محددين من أي ميزة من لوحة التحكم.
"""


def get_violation_reply(violation_type: str) -> str:
    """
    يرجع رسالة رد مناسبة حسب نوع المخالفة.
    """
    if violation_type == "contacts":
        return VIOLATION_REPLY_CONTACT
    if violation_type == "location":
        return VIOLATION_REPLY_LOCATION
    return VIOLATION_REPLY