"""
نصوص نظام المستويات.
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


def level_up_notification(full_name: str, username: str | None, new_level: int, reward: int) -> str:
    username_display = f"@{username}" if username else ""

    return (
        f"🎉 <b>رفع مستوى!</b>\n"
        f"👤 العضو: {full_name} {username_display}\n"
        f"📊 المستوى الجديد: {new_level}\n"
        f"🎁 المكافأة: {reward:,} د.ع"
    )
