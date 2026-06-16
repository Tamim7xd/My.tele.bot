"""
نظام الذكاء الاصطناعي (ai) - عميل Gemini API.

يستخدم استدعاء HTTP مباشر (عبر aiohttp، المتوفرة أصلاً كاعتماد aiogram)
بدل مكتبة google-generativeai، لتجنب مشاكل توافق الإصدارات والاعتماد
على REST API الرسمي الثابت من Google.

التعليمات (System Instruction) تفرض:
- الرد باللهجة العراقية فقط
- نص فقط، بدون أي ذكر لروابط
- رفض ذكر أي موقع/إحداثيات جغرافية حقيقية
"""

import aiohttp

from core.config import GEMINI_API_KEY


GEMINI_MODEL = "gemini-flash-lite-latest"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


SYSTEM_INSTRUCTION = (
    "انت مساعد ذكي تتكلم باللهجة العراقية فقط، دايماً وبكل ردودك، مهما كان السؤال أو اللغة المستخدمة بيه. "
    "جاوب بشكل نص فقط، قصير ومباشر (جملتين أو ثلاثة بالأكثر إلا إذا طلب الشخص تفصيل أكثر)، وبدون رموز Markdown زائدة. "
    "ممنوع نهائياً ترسل أو تذكر أي رابط (URL) أو عنوان موقع إلكتروني بأي شكل، حتى لو طلب منك المستخدم ذلك - "
    "بهذه الحالة قل بأدب إنك ما تقدر ترسل روابط. "
    "ممنوع نهائياً تذكر أو ترسل أي موقع جغرافي حقيقي (إحداثيات، خط طول وعرض، أو رابط خرائط) - "
    "إذا طلب منك أحد ذلك، اعتذر بأدب وقل ما تقدر. "
    "لا ترسل صور أو ملفات، فقط كلام نصي."
)


async def ask_gemini(question: str) -> str | None:
    """
    يرسل سؤالاً لـ Gemini ويرجع الرد النصي.
    يرجع None في حال فشل الطلب (مفتاح خاطئ، تجاوز الحصة، خطأ شبكة...).
    """
    if not GEMINI_API_KEY:
        return None

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [
            {
                "parts": [{"text": question}]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 250,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GEMINI_URL, json=payload, headers=headers, timeout=30) as response:
                if response.status != 200:
                    return None

                data = await response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])

        if not parts:
            return None

        text = parts[0].get("text", "").strip()

        return text or None

    except Exception:
        return None
