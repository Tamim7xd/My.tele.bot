"""
نصوص نظام الأرشيف.
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


CATEGORY_LABELS = {
    "violation": "⚠️ المخالفات",
    "deduct": "✂️ الخصومات",
    "reward": "🎁 المكافآت",
    "mute": "🔇 الكتم",
    "ban": "🚫 الحظر",
    "warn": "⚠️ التحذيرات",
}


def archive_main_text(full_name: str, counts: dict[str, int]) -> str:
    lines = [f"📁 <b>أرشيف {full_name}</b>", "━━━━━━━━━━━━━━━"]

    for action_type, label in CATEGORY_LABELS.items():
        lines.append(f"{label}: {counts.get(action_type, 0)}")

    lines.append("━━━━━━━━━━━━━━━")
    lines.append("اختر فئة لعرض التفاصيل:")

    return "\n".join(lines)


def category_entries_text(full_name: str, action_type: str, entries: list, total: int) -> str:
    label = CATEGORY_LABELS.get(action_type, action_type)

    if total == 0:
        return f"{label} - {full_name}\n━━━━━━━━━━━━━━━\nلا يوجد سجلات."

    lines = [f"{label} - {full_name} ({total})", "━━━━━━━━━━━━━━━"]

    for entry in entries:
        lines.append(_format_entry(action_type, entry))
        lines.append("───────────────")

    if lines and lines[-1] == "───────────────":
        lines.pop()

    return "\n".join(lines)


def _format_entry(action_type: str, entry) -> str:
    """يبني نص سجل واحد (للعرض داخل اللوحة وللنسخ)."""
    done_by_name = entry["done_by_name"] or "غير معروف"
    done_by_username = f"@{entry['done_by_username']}" if entry["done_by_username"] else ""
    date_str = entry["created_at"].strftime("%Y-%m-%d %H:%M")

    lines = []

    if action_type in ("deduct", "reward"):
        amount = entry["amount"] or 0
        lines.append(f"💰 المبلغ: {amount:,} د.ع")

    reason = entry["reason"]
    if reason:
        lines.append(f"📝 السبب: {reason}")

    replied_message = entry["replied_message"]
    if replied_message:
        lines.append(f"💬 الرسالة: «{replied_message}»")

    lines.append(f"👮 بواسطة: {done_by_name} {done_by_username}".strip())
    lines.append(f"🕒 التاريخ: {date_str}")

    return "\n".join(lines)


def category_copy_text(full_name: str, action_type: str, entries: list, total: int) -> str:
    """نص قابل للنسخ لفئة واحدة (يُرسل كرسالة منفصلة)."""
    label = CATEGORY_LABELS.get(action_type, action_type)

    if total == 0:
        return f"{label} - {full_name}\nلا يوجد سجلات."

    lines = [f"{label} - {full_name} (الإجمالي: {total})", "═══════════════"]

    for i, entry in enumerate(entries, start=1):
        lines.append(f"#{i}")
        lines.append(_format_entry(action_type, entry))
        lines.append("───────────────")

    if lines and lines[-1] == "───────────────":
        lines.pop()

    if total > len(entries):
        lines.append(f"\n... وعدد {total - len(entries)} سجل إضافي غير معروض.")

    return "\n".join(lines)


def full_summary_text(full_name: str, counts: dict[str, int]) -> str:
    """ملخص شامل (داخل اللوحة) - عرض سريع للأعداد."""
    lines = [f"📋 <b>العدد الكامل - {full_name}</b>", "━━━━━━━━━━━━━━━"]

    for action_type, label in CATEGORY_LABELS.items():
        lines.append(f"{label}: {counts.get(action_type, 0)}")

    total = sum(counts.values())
    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"الإجمالي: {total}")

    return "\n".join(lines)


def full_summary_copy_text(full_name: str, all_entries: dict[str, list], counts: dict[str, int]) -> str:
    """ملخص شامل قابل للنسخ - يحتوي كل الفئات مع تفاصيلها."""
    lines = [f"📋 الأرشيف الكامل - {full_name}", "═══════════════"]

    total = sum(counts.values())
    lines.append(f"الإجمالي: {total}")
    lines.append("")

    for action_type, label in CATEGORY_LABELS.items():
        entries = all_entries.get(action_type, [])
        count = counts.get(action_type, 0)

        lines.append(f"{label} ({count})")
        lines.append("───────────────")

        if not entries:
            lines.append("لا يوجد سجلات.")
        else:
            for i, entry in enumerate(entries, start=1):
                lines.append(f"#{i}")
                lines.append(_format_entry(action_type, entry))
                if i < len(entries):
                    lines.append("- - -")

            if count > len(entries):
                lines.append(f"... وعدد {count - len(entries)} سجل إضافي غير معروض.")

        lines.append("═══════════════")

    return "\n".join(lines)


COPY_SENT = "📋 تم إرسال النص القابل للنسخ في رسالة جديدة."
