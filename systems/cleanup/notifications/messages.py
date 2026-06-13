"""
نصوص نظام التنظيف.
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


def countdown_text(seconds_left: int) -> str:
    """نص العد التنازلي قبل التنظيف."""
    numbers = {5: "%100 ▰▰▰▰▰", 4: "%75 ▰▰▰▱▱", 3: "%50 ▰▰▱▱▱", 2: "%25 ▰▱▱▱▱", 1: "%0 ▱▱▱▱▱", 0: ""}
    emoji = numbers.get(seconds_left, str(seconds_left))

    return f" جارِ التنظيف  {emoji}"


CLEANING_NOW = "جارِ عملية التعفير 😂"


def done_text(deleted_count: int) -> str:
    """النص النهائي بعد انتهاء التنظيف."""
    return f" ▮تم تنظيف المجموعة 🫧  {deleted_count} "


NO_PERMISSION = "❌ هذا الأمر متاح للمالك والأدمن فقط."
