"""
محرك تطبيع النص الخارق (Super Text Normalizer) لنظام الحماية.

تطوير عن النسخة الأساسية، يكشف أشكال تلاعب أعمق بكثير:

1. إزالة التشكيل العربي (الحركات) و Tatweel
2. توحيد الحروف العربية المتشابهة (أ/إ/آ/ٱ -> ا، ة -> ه، ى -> ي...)
3. إزالة الفواصل الخفية: مسافات، نقاط، شرطات، Zero-Width chars
   (مسافات/فواصل غير مرئية يستخدمها المتلاعبون لخداع الفلاتر)
4. توحيد الحروف المتشابهة بصرياً بين أبجديات مختلفة (homoglyphs):
   مثل الحرف اللاتيني "a" يبدو كالعربي "ا" في بعض الخطوط، الأرقام
   الفارسية/الهندية -> أرقام عادية، الحروف الكيريلية المتشابهة بصرياً
   بالحروف اللاتينية (а -> a، е -> e...) شائعة الاستخدام للتحايل
5. تحويل أرقام شائعة بدل حروف عربية (عربيزي): 7->ح, 3->ع, 2->ء, 0->و, 8->غ
6. تقليص أي حرف متكرر 3 مرات فأكثر لمرتين فقط
7. إزالة اتجاه النص المعكوس (RTL/LTR override characters)

يُطبَّق هذا التطبيع على نص الرسالة وعلى كل كلمة في أي قائمة محظورة
(الكلمات المحظورة العادية + خيارات النظام) قبل المطابقة.
"""

import re


# ===== خرائط توحيد الحروف العربية =====

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

# أرقام فارسية/هندية (Eastern Arabic numerals) -> أرقام عادية
_EASTERN_DIGITS_MAP = {
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
}

# حروف لاتينية/كيريلية متشابهة بصرياً بحروف عربية أو لاتينية أخرى
# (homoglyphs شائعة الاستخدام للتحايل على الفلاتر)
_HOMOGLYPH_MAP = {
    # كيريلية تشبه لاتينية بصرياً
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c",
    "х": "x", "у": "y", "к": "k", "м": "m", "н": "h",
    "В": "B", "Е": "E", "А": "A", "О": "O", "Р": "P",
    "С": "C", "Х": "X", "У": "Y", "К": "K", "М": "M",
    # حروف لاتينية شائعة الاستخدام بدل عربية في كتابة "عربيزي"
    "@": "ا",
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

# رموز غير مرئية (Zero-Width) ورموز اتجاه النص المستخدمة للتحايل
_INVISIBLE_CHARS = re.compile(
    "[" + "".join([
        "\u200B",  # Zero Width Space
        "\u200C",  # Zero Width Non-Joiner
        "\u200D",  # Zero Width Joiner
        "\u200E",  # Left-to-Right Mark
        "\u200F",  # Right-to-Left Mark
        "\u202A", "\u202B", "\u202C", "\u202D", "\u202E",  # Embedding/Override
        "\uFEFF",  # Zero Width No-Break Space (BOM)
        "\u00AD",  # Soft Hyphen
    ]) + "]"
)


def normalize_text(text: str) -> str:
    """
    يطبّع نصاً عربياً (أو مختلطاً) للمطابقة مع الكلمات المحظورة،
    بأقوى مستوى ممكن لكشف التلاعب.
    """
    if not text:
        return ""

    result = text.lower()

    # إزالة الرموز غير المرئية أولاً (قبل أي معالجة أخرى)
    result = _INVISIBLE_CHARS.sub("", result)

    # إزالة التشكيل
    result = _ARABIC_DIACRITICS.sub("", result)

    # توحيد الأرقام الفارسية/الهندية لأرقام عادية
    for src, dst in _EASTERN_DIGITS_MAP.items():
        result = result.replace(src, dst)

    # توحيد الحروف المتشابهة بصرياً (homoglyphs) قبل المعالجة العربية
    for src, dst in _HOMOGLYPH_MAP.items():
        result = result.replace(src, dst)

    # توحيد الحروف العربية المتشابهة
    for src, dst in _ARABIC_NORMALIZATION_MAP.items():
        result = result.replace(src, dst)

    # استبدال الأرقام الشائعة بحروف عربية (عربيزي)
    for src, dst in _LEET_MAP.items():
        result = result.replace(src, dst)

    # إزالة كل ما ليس حرفاً عربياً أو لاتينياً (مسافات، نقاط، رموز...)
    result = re.sub(r"[^\u0600-\u06FFa-z]", "", result)

    # تقليص أي حرف متكرر مرتين فأكثر -> حرف واحد فقط (لكشف "أحببببك" -> "احبك")
    result = re.sub(r"(.)\1+", r"\1", result)

    return result


def contains_word(normalized_text: str, normalized_word: str) -> bool:
    """يتحقق إن كانت الكلمة المطبَّعة موجودة كسلسلة فرعية داخل النص المطبَّع."""
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
