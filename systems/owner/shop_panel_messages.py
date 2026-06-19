"""
نصوص "🛒 المتجر" في لوحة التحكم.
"""


SHOP_MAIN_TEXT = "🛒 <b>إدارة المتجر</b>\n━━━━━━━━━━━━━━━\nاختر ما تريد إدارته:"


def membership_admin_text(membership: dict) -> str:
    from systems.shop.queries import format_duration

    duration_text = format_duration(membership.get("duration_seconds", 0))

    return (
        f"👑 <b>{membership['name']}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 السعر: {membership['price']:,} د.ع\n"
        f"⏳ المدة: {duration_text}\n"
        f"🎁 المكافأة اليومية: {membership['daily_reward']:,} د.ع\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر ما تريد تعديله:"
    )


NAME_PROMPT = "✏️ أرسل الاسم الجديد."

PRICE_PROMPT = "💰 أرسل السعر الجديد (يدعم صيغة 1.000)."

REWARD_PROMPT = "🎁 أرسل قيمة المكافأة اليومية الجديدة (0 لإيقافها)."

DURATION_VALUE_PROMPT = "⏳ أرسل الرقم (مثال: 7 لو اختياك أيام = أسبوع)."

INVALID_NUMBER = "❌ يجب إرسال رقم صحيح."


def updated_text(field: str) -> str:
    return f"✅ تم تحديث {field}."


def membership_features_text(membership: dict) -> str:
    return f"⚙️ <b>مزايا {membership['name']}</b>\n━━━━━━━━━━━━━━━\nاضغط لتبديل أي ميزة:"


# ===== من اشترى عضوية =====

def owners_list_text(membership_name: str, total: int, owners: list) -> str:
    if total == 0:
        return f"📋 <b>من اشترى {membership_name}</b>\n━━━━━━━━━━━━━━━\nلا يوجد مشترون حتى الآن."

    lines = [f"📋 <b>من اشترى {membership_name}</b> ({total})", "━━━━━━━━━━━━━━━"]

    for owner in owners:
        username_display = f"@{owner['username']}" if owner["username"] else ""
        date_str = owner["created_at"].strftime("%Y-%m-%d")
        lines.append(f"• {owner['full_name']} {username_display} — {date_str}")

    return "\n".join(lines)


# ===== الألقاب =====

def title_admin_text(title: dict) -> str:
    return f"🏷️ <b>{title['name']}</b>\n━━━━━━━━━━━━━━━\n💰 السعر: {title['price']:,} د.ع"


# ===== إعدادات مسح المحادثة =====

def clear_settings_text(price: int, range_count: int) -> str:
    return (
        f"🗑️ <b>إعدادات مسح المحادثة</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 السعر: {price:,} د.ع\n"
        f"🔢 نطاق الحذف: آخر {range_count} رسالة\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر ما تريد تعديله:"
    )


CLEAR_PRICE_PROMPT = "✏️ أرسل السعر الجديد لمسح المحادثة (يدعم صيغة 1.000)."

CLEAR_RANGE_PROMPT = "✏️ أرسل عدد الرسائل الجديد لنطاق المسح."


# ===== أرشيف المتجر =====

ARCHIVE_MAIN_TEXT = "📁 <b>أرشيف المتجر</b>\n━━━━━━━━━━━━━━━\nاختر سجلاً لعرضه:"


def clear_archive_list_text(total: int) -> str:
    if total == 0:
        return "🗑️ <b>سجل مسح المحادثات</b>\n━━━━━━━━━━━━━━━\nلا يوجد سجلات حتى الآن."

    return f"🗑️ <b>سجل مسح المحادثات</b> ({total} عضو)\n━━━━━━━━━━━━━━━\nاختر عضواً:"


def clear_member_history_text(full_name: str, entries: list, total: int) -> str:
    if not entries:
        return f"🗑️ <b>{full_name}</b>\n━━━━━━━━━━━━━━━\nلا يوجد سجلات."

    lines = [f"🗑️ <b>سجل مسح {full_name}</b> ({total})", "━━━━━━━━━━━━━━━"]

    for entry in entries:
        date_str = entry["created_at"].strftime("%Y-%m-%d %H:%M")
        lines.append(f"• حذف {entry['deleted_count']} رسالة — {date_str}")

    return "\n".join(lines)


# ===== إجراءات العضوية من صفحة العضو =====

def member_membership_text(full_name: str, membership_info: dict | None) -> str:
    if membership_info is None:
        return f"👑 <b>عضوية {full_name}</b>\n━━━━━━━━━━━━━━━\nلا يملك عضوية حالياً."

    status = "✅ فعّالة" if membership_info["is_active"] else "❌ منتهية"
    expires_at = membership_info["expires_at"]
    expires_str = expires_at.strftime("%Y-%m-%d %H:%M") if expires_at else "بلا انتهاء (دائمة)"

    return (
        f"👑 <b>عضوية {full_name}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 العضوية: {membership_info['membership_id']}\n"
        f"📊 الحالة: {status}\n"
        f"📅 تنتهي: {expires_str}\n"
    )


MEMBERSHIP_REVOKED = "✅ تم سحب العضوية."

MEMBERSHIP_EXTEND_PROMPT = "✏️ أرسل عدد الأيام الإضافية (رقم صحيح، يمكن سالباً للتقليص)."

NO_ACTIVE_MEMBERSHIP_TO_EXTEND = "❌ هذا العضو لا يملك عضوية لتمديدها."


def membership_extended_text(new_expires_str: str) -> str:
    return f"✅ تم التمديد. تنتهي العضوية الآن في: {new_expires_str}"
