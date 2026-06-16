"""
نظام الذكاء الاصطناعي (ai) - الملف الرئيسي.

كلمات التشغيل: "ذكاء"، "بوت"، "كت" (أي منها + السؤال بعدها)
مثال: "بوت شلونك" أو "ذكاء وين بغداد"

القيود المفروضة:
- اللهجة العراقية فقط (عبر System Instruction في gemini_client.py)
- نص فقط، بدون صور/ملفات (الـ API نص فقط أصلاً)
- إزالة أي رابط أو إحداثيات من الرد (شبكة أمان إضافية في response_filter.py)

⚠️ ملاحظة عن الترتيب:
يستخدم F.text بشرط بدء النص بكلمة محددة، فلا يطابق كل الرسائل.
يُسجَّل مع باقي الأنظمة ذات الأوامر المحددة، قبل protection/members.
"""

from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message

from systems.ai.gemini_client import ask_gemini
from systems.ai.response_filter import sanitize_response
from systems.ai.notifications import messages


router = Router(name="ai")


TRIGGER_WORDS = ["ذكاء", "بوت", "كت"]


def _extract_question(text: str) -> str | None:
    """
    يستخرج السؤال من النص إن بدأ بأحد كلمات التشغيل.
    يرجع None إن لم يبدأ بأي منها.
    """
    stripped = text.strip()

    for word in TRIGGER_WORDS:
        if stripped == word:
            return ""

        if stripped.startswith(word + " "):
            return stripped[len(word):].strip()

    return None


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def handle_ai_trigger(message: Message) -> None:
    if message.from_user is None or message.text is None:
        raise SkipHandler

    question = _extract_question(message.text)

    if question is None:
        raise SkipHandler

    if not question:
        await message.reply(messages.EMPTY_QUESTION)
        return

    answer = await ask_gemini(question)

    if answer is None:
        await message.reply(messages.ERROR_TEXT)
        return

    safe_answer = sanitize_response(answer)

    if not safe_answer:
        await message.reply(messages.ERROR_TEXT)
        return

    await message.reply(safe_answer)
