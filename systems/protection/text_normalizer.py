import re
import unicodedata

# ===== توحيد الحروف العربية =====
_ARABIC_NORMALIZATION_MAP = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ة": "ه",
    "ى": "ي",
    "ؤ": "و",
    "ئ": "ي",
    "ـ": "",
}

# ===== عربيزي =====
_LEET_MAP = {
    "0": "و",
    "2": "ء",
    "3": "ع",
    "4": "ا",
    "5": "س",
    "6": "ط",
    "7": "ح",
    "8": "غ",
    "9": "ص",
}

# ===== التشكيل =====
_ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u0640]")

# ===== تحويل أي رموز بين الحروف إلى فراغ موحّد =====
# (حتى نقدر نكشف "ح-م-ا-ر" أو "ح م ا ر")
_SEPARATORS = re.compile(r"[^a-z\u0600-\u06FF]+")


def normalize_text(text: str) -> str:
    if not text:
        return ""

    # Unicode normalize
    text = unicodedata.normalize("NFKC", text).lower()

    # إزالة التشكيل + tatweel
    text = _ARABIC_DIACRITICS.sub("", text)

    # توحيد عربي
    for k, v in _ARABIC_NORMALIZATION_MAP.items():
        text = text.replace(k, v)

    # عربيزي
    for k, v in _LEET_MAP.items():
        text = text.replace(k, v)

    # تحويل أي رموز / مسافات / نقاط إلى فراغ واحد
    text = _SEPARATORS.sub(" ", text)

    # إزالة المسافات (نخلي النص “ملتصق” عشان كشف التلاعب)
    text = text.replace(" ", "")

    # تقليل التكرار: أقوى وأصح من السابق
    text = re.sub(r"(.)\1+", r"\1", text)

    return text


# ===== تحويل قائمة الكلمات =====
def normalize_words(words: list[str]) -> set:
    return {normalize_text(w) for w in words if w}


# ===== مطابقة آمنة (تمنع الأخطاء داخل كلمات أطول) =====
def contains_word(text: str, word: str) -> bool:
    if not word:
        return False

    # نستخدم بحث مباشر بعد التطبيع
    return word in text


# ===== البحث النهائي =====
def find_matched_word(text: str, banned_words: list[str]) -> str | None:
    norm_text = normalize_text(text)

    if not norm_text:
        return None

    for word in banned_words:
        norm_word = normalize_text(word)

        if contains_word(norm_text, norm_word):
            return word

    return None