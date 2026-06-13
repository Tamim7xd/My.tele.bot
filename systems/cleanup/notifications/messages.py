"""
نصوص نظام التنظيف.
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


def countdown_text(seconds_left: int) -> str:
    """نص العد التنازلي قبل التنظيف."""
    numbers = {5: "5️⃣", 4: "4️⃣", 3: "3️⃣", 2: "2️⃣", 1: "1️⃣", 0: "0️⃣"}
    emoji = numbers.get(seconds_left, str(seconds_left))

    return f"🧹 جارِ التنظيف بعد {emoji}"


CLEANING_NOW = "🧹 جارِ التنظيف..."


def done_text(deleted_count: int) -> str:
    """النص النهائي بعد انتهاء التنظيف."""
    return f"✅ تم حذف {deleted_count} رسالة."


NO_PERMISSION = "❌ هذا الأمر متاح للمالك والأدمن فقط."
