"""
نصوص نظام المتجر (shop).
"""


MAIN_MENU_TEXT = "🛒 <b>المتجر</b>\n━━━━━━━━━━━━━━━\nاختر ما تريد:"


# ===== مسح المخالفات/المحادثة =====

def clear_chat_intro_text(price: int) -> str:
    return (
        f"🗑️ <b>مسح محادثتي</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 السعر: {price:,} د.ع\n"
        f"━━━━━━━━━━━━━━━\n"
        f"سيتم حذف رسائلك الأخيرة من المجموعة."
    )


INSUFFICIENT_BALANCE = "❌ رصيدك ما يكفي."

CLEAR_CHAT_NO_MEMBERSHIP = "❌ تحتاج عضوية تتيح هذه الميزة لاستخدام أمر المسح."


def clear_chat_done_text(deleted_count: int) -> str:
    return f"✅ تم حذف {deleted_count} رسالة من رسائلك."


# ===== العضويات =====

def memberships_list_text() -> str:
    return "👑 <b>العضويات</b>\n━━━━━━━━━━━━━━━\nاختر عضوية لعرض تفاصيلها:"


def membership_details_text(membership: dict) -> str:
    from systems.shop.queries import format_duration

    name = membership["name"]
    price = membership["price"]
    duration_text = format_duration(membership.get("duration_seconds", 0))
    daily_reward = membership["daily_reward"]

    features = []

    if membership.get("can_clear_chat"):
        features.append("🗑️ يمكنك مسح محادثتك بأمر «مسح»")

    if daily_reward:
        features.append(f"🎁 مكافأة يومية تلقائية: {daily_reward:,} د.ع")

    if membership.get("can_send_media"):
        features.append("📎 يمكنك إرسال الوسائط (صور/فيديو/ملفات)")

    if membership.get("no_replies"):
        features.append("🚫 لا يمكن لغير الإداريين الرد على رسائلك")

    features_text = "\n".join(f"• {f}" for f in features)

    return (
        f"👑 <b>{name}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 السعر: {price:,} د.ع\n"
        f"📅 المدة: {duration_text}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>المزايا:</b>\n{features_text}"
    )


def membership_purchased_text(name: str, expires_at_str: str) -> str:
    return f"✅ تم تفعيل عضوية {name}!\n📅 تنتهي في: {expires_at_str}"


MEMBERSHIP_ALREADY_ACTIVE = "❌ لديك عضوية فعّالة بالفعل. انتظر انتهاءها قبل شراء عضوية جديدة."


# ===== الألقاب =====

def titles_list_text() -> str:
    return "🏷️ <b>الألقاب</b>\n━━━━━━━━━━━━━━━\nاختر لقباً:"


def title_details_text(title: dict, already_owned: bool) -> str:
    status = "✅ مملوك" if already_owned else f"💰 السعر: {title['price']:,} د.ع"

    return f"🏷️ <b>{title['name']}</b>\n━━━━━━━━━━━━━━━\n{status}"


def title_purchased_text(name: str) -> str:
    return f"✅ تم شراء لقب {name}!"


TITLE_ALREADY_OWNED = "✅ هذا اللقب مملوك لك بالفعل."


# ===== أمر "عضوية"/"عضويتي" =====

def my_membership_text(membership: dict | None, expires_at_str: str | None) -> str:
    if membership is None:
        return "❌ لا تملك عضوية فعّالة حالياً.\nاستخدم «سوق» لشراء عضوية."

    return membership_details_text(membership) + f"\n📅 تنتهي في: {expires_at_str}"


# ===== أمر "لقب"/"القاب"/"مشتريات"/"مشترياتي" =====

def my_titles_text(owned_titles: list[dict], active_title_id: str | None) -> str:
    if not owned_titles:
        return "❌ لا تملك أي لقب حالياً.\nاستخدم «سوق» لشراء لقب."

    lines = ["🏷️ <b>ألقابك</b>", "━━━━━━━━━━━━━━━"]

    for title in owned_titles:
        marker = "✅" if title["id"] == active_title_id else "▫️"
        lines.append(f"{marker} {title['name']}")

    lines.append("━━━━━━━━━━━━━━━")
    lines.append("اختر لقباً لتفعيله في ملفك:")

    return "\n".join(lines)


def title_activated_text(name: str) -> str:
    return f"✅ تم تفعيل لقب {name} في ملفك الشخصي."


# ===== إشعارات المجموعة عند الشراء =====

def membership_purchase_group_notification(full_name: str, membership_name: str, price: int) -> str:
    return (
        f"🛒 <b>{full_name}</b> اشترى عضوية <b>{membership_name}</b>\n"
        f"💰 السعر: {price:,} د.ع"
    )


def title_purchase_group_notification(full_name: str, title_name: str, price: int) -> str:
    return (
        f"🏷️ <b>{full_name}</b> اشترى لقب <b>{title_name}</b>\n"
        f"💰 السعر: {price:,} د.ع"
    )