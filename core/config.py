"""
ملف الإعدادات العامة للبوت
يقرأ جميع المتغيرات السرية والإعدادات من ملف .env
"""

import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# ===== المتغيرات الأساسية =====

# توكن البوت من @BotFather
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# رابط الاتصال بقاعدة بيانات PostgreSQL (من Railway)
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# رابط الاتصال بـ Redis (من Railway) - اختياري
REDIS_URL: str = os.getenv("REDIS_URL", "")

# مفتاح Gemini API للذكاء الاصطناعي
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# آيدي المالك (الأدمن الأساسي) - يجب أن يكون رقم
OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))


# ===== إعدادات عامة قابلة للتعديل =====

# مدة اختفاء رسائل الأوامر والقوائم (بالثواني)
DEFAULT_DELETE_DELAY: int = 5


# ===== التحقق من وجود المتغيرات الأساسية =====

def validate_config() -> None:
    """
    يتحقق من أن جميع المتغيرات الأساسية موجودة قبل تشغيل البوت.
    يرفع خطأ واضح إذا كان أي متغير أساسي مفقوداً.
    """
    missing = []

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not DATABASE_URL:
        missing.append("DATABASE_URL")
    if not OWNER_ID:
        missing.append("OWNER_ID")

    if missing:
        raise ValueError(
            "❌ المتغيرات التالية مفقودة في ملف .env: " + ", ".join(missing)
        )
