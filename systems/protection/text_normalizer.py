import re
from core.config import Config
from systems.ai.gemini_client import analyze_content_with_gemini
from systems.protection.queries import get_cached_protection_settings, log_to_advanced_archive

def normalize_text(text):
    """تنظيف النصوص وتوحيدها البرمجي لمنع التلاعب"""
    if not text:
        return ""
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'[ىي]', 'ي', text)
    text = re.sub(r'[هة]', 'ه', text)
    return text.strip().lower()

def inspect_message(bot, message):
    """الفحص فائق السرعة عبر الكاش والذكاء الاصطناعي متعدد الوسائط"""
    chat_id = message.chat.id
    raw_text = message.text or ""
    
    # جلب الإعدادات من الذاكرة المؤقتة (الكاش) فورا دون لمس قاعدة البيانات
    settings = get_cached_protection_settings(chat_id)
    
    if not settings['enabled']:
        return True

    # 1. فحص الكلمات المحظورة عبر الكاش (سرعة فائقة)
    normalized = normalize_text(raw_text)
    for bad_word in settings.get('blocked_words', []):
        if bad_word in normalized:
            trigger_archive_flow(bot, message, reason=f"كلمة محظورة كاش ({bad_word})")
            return False

    # 2. فحص سياق النص بالذكاء الاصطناعي (Gemini)
    if settings['ai_enabled'] and raw_text:
        is_safe, reason = analyze_content_with_gemini(raw_text, strictness=settings['strictness'])
        if not is_safe:
            trigger_archive_flow(bot, message, reason=f"تحليل سياقي ذكي: {reason}")
            return False

    return True

def trigger_archive_flow(bot, message, reason):
    """حذف فوري وتوليد التقرير التفاعلي للأرشيف"""
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    
    log_to_advanced_archive(bot, message, reason)
