"""
نصوص نظام التحويل (transfer).
"""


NO_REPLY = "↩️ يجب الرد على رسالة العضو المراد التحويل إليه."

SELF_TRANSFER = "❌ لا يمكنك تحويل رصيد لنفسك."

TARGET_NOT_FOUND = "❌ العضو غير مسجل في النظام."

INVALID_AMOUNT = "❌ المبلغ غير صحيح. أمثلة: 1000، 1.000، 1،000"

BELOW_MIN = "❌ الحد الأدنى للتحويل: {min:,} د.ع"

ABOVE_MAX = "❌ الحد الأقصى للتحويل: {max:,} د.ع"

INSUFFICIENT_BALANCE = "❌ رصيدك غير كافٍ للتحويل."


def confirm_text(target_name: str, amount: int, fee: int, final_amount: int) -> str:
    fee_line = f"💸 الرسوم ({fee}%): {amount - final_amount:,} د.ع\n" if fee > 0 else ""
    return (
        f"💸 <b>تأكيد التحويل</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 إلى: {target_name}\n"
        f"💰 المبلغ: {amount:,} د.ع\n"
        f"{fee_line}"
        f"✅ سيصل: {final_amount:,} د.ع\n"
        f"━━━━━━━━━━━━━━━\n"
        f"هل تؤكد التحويل؟"
    )


def success_text(target_name: str, final_amount: int, new_balance: int) -> str:
    return (
        f"✅ تم التحويل بنجاح!\n"
        f"👤 إلى: {target_name}\n"
        f"💰 المبلغ: {final_amount:,} د.ع\n"
        f"💳 رصيدك الجديد: {new_balance:,} د.ع"
    )


def received_text(sender_name: str, amount: int, new_balance: int) -> str:
    return (
        f"🎁 استلمت تحويلاً!\n"
        f"👤 من: {sender_name}\n"
        f"💰 المبلغ: {amount:,} د.ع\n"
        f"💳 رصيدك الجديد: {new_balance:,} د.ع"
    )
