from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from systems.protection.queries import get_cached_protection_settings, PROTECTION_CACHE

def get_protection_panel_keyboard(chat_id):
    """توليد أزرار لوحة التحكم بالتوافق مع نظام الكاش والأرشيف المتقدم"""
    settings = get_cached_protection_settings(chat_id)
    
    status_text = "🟢 نشط (كاش)" if settings['enabled'] else "🔴 معطل"
    ai_status_text = "🟢 نشط" if settings['ai_enabled'] else "🔴 معطل"
    strictness_text = f"⚙️ صرامة الـ AI: {settings['strictness']}"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    markup.add(
        InlineKeyboardButton(f"نظام الحماية: {status_text}", callback_data=f"toggle_prot_{chat_id}"),
        InlineKeyboardButton(f"مراقبة الذكاء الاصطناعي: {ai_status_text}", callback_data=f"toggle_ai_prot_{chat_id}"),
        InlineKeyboardButton(strictness_text, callback_data=f"cycle_strictness_{chat_id}"),
        InlineKeyboardButton("⚡ استهلاك قاعدة البيانات: 0% (كاش مفعّل)", callback_data="none"),
        InlineKeyboardButton("↩️ العودة للوحة الرئيسية", callback_data="back_to_main_panel")
    )
    return markup

def handle_protection_callback(bot, call):
    data = call.data
    chat_id = call.message.chat.id
    
    if data.startswith("toggle_prot_"):
        settings = get_cached_protection_settings(chat_id)
        settings['enabled'] = not settings['enabled'] # تحديث الكاش الفوري
        bot.answer_callback_query(call.id, "تم تحديث حالة الحماية في الكاش")
        
    elif data.startswith("toggle_ai_prot_"):
        settings = get_cached_protection_settings(chat_id)
        settings['ai_enabled'] = not settings['ai_enabled']
        bot.answer_callback_query(call.id, "تم تحديث وضع الذكاء الاصطناعي")
        
    elif data.startswith("cycle_strictness_"):
        settings = get_cached_protection_settings(chat_id)
        levels = ["Low", "Medium", "Strict"]
        next_idx = (levels.index(settings['strictness']) + 1) % len(levels)
        settings['strictness'] = levels[next_idx]
        bot.answer_callback_query(call.id, f"الصرامة الحالية: {levels[next_idx]}")
        
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_protection_panel_keyboard(chat_id))
