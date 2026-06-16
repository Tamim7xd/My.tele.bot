"""
فلتر أمان لرد الذكاء الاصطناعي.

حتى مع التعليمات (System Instruction)، النماذج قد تتجاوزها أحياناً.
هذا الفلتر شبكة أمان إضافية: يحذف أي رابط أو إحداثيات قد تظهر
في الرد قبل إرساله للمجموعة.
"""

import re


_URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)",
    re.IGNORECASE,
)

_COORDINATES_PATTERN = re.compile(
    r"-?\d{1,3}\.\d+\s*,\s*-?\d{1,3}\.\d+"
)


def sanitize_response(text: str) -> str:
    """يزيل أي رابط أو إحداثيات من رد الذكاء الاصطناعي قبل إرساله."""
    text = _URL_PATTERN.sub("", text)
    text = _COORDINATES_PATTERN.sub("", text)

    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def contains_blocked_content(text: str) -> bool:
    """يتحقق إن كان النص يحتوي رابطاً أو إحداثيات (للمراقبة فقط)."""
    return bool(_URL_PATTERN.search(text) or _COORDINATES_PATTERN.search(text))
