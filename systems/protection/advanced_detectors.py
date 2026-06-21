"""
كاشفات متقدمة لنظام الحماية:
- روابط مموهة (hxxp، [.]، "نقطة كوم" نصياً، إلخ)
- أرقام هواتف دولية (كل الصيغ + المفاتيح الدولية)
"""

import re


# ===== الروابط (بكل أصنافها وأشكال التمويه) =====

_URL_PATTERNS = [
    re.compile(r"https?://\S+", re.IGNORECASE),
    re.compile(r"www\.\S+", re.IGNORECASE),
    re.compile(r"t\.me/\S+", re.IGNORECASE),
    re.compile(r"telegram\.me/\S+", re.IGNORECASE),
    # تمويه شائع: hxxp, h**p, htt ps
    re.compile(r"h[\s\*_\-]*t[\s\*_\-]*t[\s\*_\-]*p[\s\*_\-]*s?[\s\*_\-]*:?[\s\*_\-]*//", re.IGNORECASE),
    # نطاقات بصيغة مموهة: example[.]com / example(dot)com / example نقطة كوم
    re.compile(r"\b[a-zA-Z0-9-]+\s*[\[\(]?\s*(?:\.|dot|نقطة)\s*[\]\)]?\s*(com|net|org|io|me|co|info|xyz|app|link)\b", re.IGNORECASE),
    # نطاقات عادية بامتداد معروف (مثال: example.com بدون بروتوكول)
    re.compile(r"\b[a-zA-Z0-9-]+\.(com|net|org|io|me|co|info|xyz|app|link|gg|tv)\b", re.IGNORECASE),
]


def contains_url(text: str) -> bool:
    """يتحقق إن كان النص يحتوي رابطاً بأي صيغة (عادية أو مموهة)."""
    for pattern in _URL_PATTERNS:
        if pattern.search(text):
            return True

    return False


# ===== أرقام الهواتف (كل الدول والصيغ + المفاتيح الدولية) =====

# نمط عام لرقم هاتف دولي: + أو 00 متبوعة بمفتاح دولي (1-3 أرقام)
# ثم 6-12 رقم إضافي، يسمح بفواصل (مسافة/شرطة/قوس) بين المجموعات
_PHONE_PATTERN = re.compile(
    r"(?:\+|00)\d{1,3}[\s\-\(\)]{0,3}\d{2,4}[\s\-\(\)]{0,3}\d{2,4}[\s\-\(\)]{0,3}\d{0,4}"
)

# أرقام محلية طويلة بدون مفتاح دولي لكن بصيغة هاتف واضحة (7-11 رقم متتالي
# مع فواصل اختيارية) - يُستخدم بحذر أكبر لتقليل الإيجابيات الكاذبة
_LOCAL_PHONE_PATTERN = re.compile(
    r"\b\d{3}[\s\-]?\d{3}[\s\-]?\d{4,5}\b"
)


def contains_phone_number(text: str) -> bool:
    """يتحقق إن كان النص يحتوي رقم هاتف (دولي بمفتاح، أو محلي بصيغة واضحة)."""
    if _PHONE_PATTERN.search(text):
        return True

    if _LOCAL_PHONE_PATTERN.search(text):
        return True

    return False
