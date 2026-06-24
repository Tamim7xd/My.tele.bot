"""
نصوص نظام التفاعل التلقائي.
"""


def member_menu_text(full_name: str) -> str:
    return f"👋 أهلاً {full_name}!\n━━━━━━━━━━━━━━━\nاختر ما تريد:"


def staff_menu_text(full_name: str, rank: str) -> str:
    rank_label = "👮 أدمن" if rank == "admin" else "🛡️ مشرف"
    return f"👋 أهلاً {full_name}! ({rank_label})\n━━━━━━━━━━━━━━━\nاختر ما تريد:"


NEED_START = "⚠️ لفتح قائمتك الشخصية، ابدأ محادثة مع البوت أولاً ثم اضغط الزر مجدداً."

MENU_OPENED = "✅ تم فتح قائمتك في الخاص!"
