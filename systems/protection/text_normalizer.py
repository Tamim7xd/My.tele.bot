"""
محرك تطبيع النص (Text Normalization) لنظام الحماية.

الهدف: كشف الكلمات المحظورة حتى مع التلاعب الشائع:
- التشكيل (الحركات): إزالتها
- توحيد الحروف المتشابهة: أ/إ/آ/ٱ -> ا، ة -> ه، ى -> ي، ؤ -> و، ئ -> ي
- إزالة الفواصل بين الحروف: مسافات، نقاط، شرطات سفلية، Tatweel (ـ)، أي رمز غير حرف
- تقليص التكرار: "ححححرف" -> "حرف"
- تحويل أرقام شائعة الاستخدام بدل حروف (عربيزي): 7->ح, 3->ع, 2->ء, 0->و, 8->غ

يُطبَّق هذا التطبيع على نص الرسالة وعلى كل كلمة في القائمة المحظورة
قبل المطابقة، فتُكشف معظم أشكال التلاعب.

⚠️ هذا الملف لا يحتوي على أي قائمة كلمات افتراضية - القائمة بالكامل
يديرها المالك من لوحة التحكم.
"""

import re


# ===== خرائط توحيد الحروف =====

_ARABIC_NORMALIZATION_MAP = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ة": "ه",
    "ى": "ي",
    "ؤ": "و",
    "ئ": "ي",
}

# أرقام شائعة بدل حروف (عربيزي)
_LEET_MAP = {
    "0": "و",
    "2": "ء",
    "3": "ع",
    "4": "ا",
    "5": "س",
    "6": "ط",
    "7": "ح",
    "8": "غ",
}

# تشكيل عربي (حركات) و Tatweel لإزالته
_ARABIC_DIACRITICS = re.compile(
    "[" + "".join([
        "\u064B", "\u064C", "\u064D", "\u064E", "\u064F",
        "\u0650", "\u0651", "\u0652", "\u0653", "\u0654",
        "\u0655", "\u0656", "\u0657", "\u0658", "\u0659",
        "\u065A", "\u065B", "\u065C", "\u065D", "\u065E",
        "\u065F", "\u0670",
        "\u0640",
    ]) + "]"
)


def normalize_text(text: str) -> str:
    """
    يطبّع نصاً عربياً (أو مختلطاً) للمطابقة مع الكلمات المحظورة.

    الخطوات:
    1. تحويل لحروف صغيرة (للنص اللاتيني)
    2. إزالة التشكيل و Tatweel
    3. توحيد الحروف العربية المتشابهة
    4. استبدال الأرقام الشائعة بحروف عربية مقابلة
    5. إزالة كل ما ليس حرفاً عربياً أو لاتينياً (مسافات، نقاط، رموز...)
    6. تقليص أي حرف متكرر أكثر من مرتين إلى مرتين فقط
    """
    if not text:
        return ""

    result = text.lower()

    result = _ARABIC_DIACRITICS.sub("", result)

    for src, dst in _ARABIC_NORMALIZATION_MAP.items():
        result = result.replace(src, dst)

    for src, dst in _LEET_MAP.items():
        result = result.replace(src, dst)

    result = re.sub(r"[^\u0600-\u06FFa-z]", "", result)

    result = re.sub(r"(.)\1{2,}", r"\1\1", result)

    return result


def contains_word(normalized_text: str, normalized_word: str) -> bool:
    """
    يتحقق إن كانت الكلمة المطبَّعة موجودة كسلسلة فرعية داخل النص المطبَّع.
    """
    if not normalized_word:
        return False

    return normalized_word in normalized_text


def find_matched_word(text: str, banned_words: list[str]) -> str | None:
    """
    يفحص نصاً مقابل قائمة كلمات محظورة (بعد تطبيع الجميع).
    يرجع الكلمة المحظورة (الأصلية كما أُدخلت) عند أول تطابق، أو None.
    """
    normalized_text = normalize_text(text)

    if not normalized_text:
        return None

    for word in banned_words:
        normalized_word = normalize_text(word)

        if contains_word(normalized_text, normalized_word):
            return word

    return None
