"""
تطبيع النص لكشف الكلمات المحظورة
"""

import re

# توحيد الحروف
_ARABIC_NORMALIZATION = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي",
}

# العربيزي - تحويل الأرقام إلى حروف
_LEET_MAP = {
    "0": "و", "2": "ء", "3": "ع", "4": "ا",
    "5": "س", "6": "ط", "7": "ح", "8": "غ",
    "9": "ق", "@": "ا", "$": "س", "1": "ا",
    "&": "و", "!": "ا",
}

# التشكيل والحركات
_DIACRITICS = re.compile("[" + "".join([
    "\u064B", "\u064C", "\u064D", "\u064E", "\u064F",
    "\u0650", "\u0651", "\u0652", "\u0653", "\u0654",
    "\u0655", "\u0656", "\u0657", "\u0658", "\u0659",
    "\u065A", "\u065B", "\u065C", "\u065D", "\u065E",
    "\u065F", "\u0670", "\u0640",
]) + "]")


def normalize_text(text: str) -> str:
    """تطبيع النص"""
    if not text:
        return ""
    
    result = text.lower()
    result = _DIACRITICS.sub("", result)
    
    for src, dst in _ARABIC_NORMALIZATION.items():
        result = result.replace(src, dst)
    
    for src, dst in _LEET_MAP.items():
        result = result.replace(src, dst)
    
    result = re.sub(r"[^\u0600-\u06FFa-z]", "", result)
    result = re.sub(r"(.)\1{2,}", r"\1\1", result)
    
    return result


def find_matched_word(text: str, banned_words: list) -> str | None:
    """البحث عن كلمة محظورة في النص"""
    normalized_text = normalize_text(text)
    
    if not normalized_text:
        return None
    
    for word in banned_words:
        normalized_word = normalize_text(word)
        
        if normalized_word in normalized_text:
            return word
        
        text_no_spaces = re.sub(r"\s+", "", normalized_text)
        if normalized_word in text_no_spaces:
            return word
    
    return None