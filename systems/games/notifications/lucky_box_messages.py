"""
نصوص صندوق الحظ (lucky_box).
"""


INTRO_TEXT = "📦 <b>صندوق الحظ</b>\n━━━━━━━━━━━━━━━\nجرب حظك!"

INSUFFICIENT_BALANCE = "❌ رصيدك ما يكفي لدفع رسوم الدخول."


def result_text(won_amount: int, net: int) -> str:
    if net > 0:
        return f"🎉 فتحت الصندوق وربحت {won_amount:,} د.ع!\n📈 الصافي: +{net:,} د.ع"
    elif net == 0:
        return f"📦 فتحت الصندوق واسترجعت {won_amount:,} د.ع.\n⚖️ تعادل."
    elif won_amount == 0:
        return "💨 فتحت الصندوق... وكان فاضي! خسرت رسوم الدخول."
    else:
        return f"📦 فتحت الصندوق وحصلت على {won_amount:,} د.ع.\n📉 الصافي: {net:,} د.ع"
