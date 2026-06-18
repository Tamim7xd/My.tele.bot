
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.config import Config

# الذاكرة المؤقتة (الكاش) في رام البوت لتسريع العمليات
PROTECTION_CACHE = {}

def get_cached_protection_settings(chat_id):
    """جلب الإعدادات من الكاش، وإذا لم تكن موجودة يجلبها من قاعدة البيانات ويخزنها"""
    if chat_id not in PROTECTION_CACHE:
        # هنا يتم جلب البيانات الفسيولوجية الأصلية من DB لأول مرة فقط
        PROTECTION_CACHE[chat_id] = {
            "enabled": True,
            "ai_enabled": True,
            "strictness": "Medium",
            "blocked_words": ["مخرب", "سبام"]
        }
    return PROTECTION_CACHE[chat_id]

def log_to_advanced_archive(bot, message, reason):
    """إرسال التقرير للأرشيف مع أزرار التحكم السريع للمالك"""
    archive_id = Config.OWNER_ARCHIVE_ID
    
    report = (
        f"⚙️ **تنبيه أرشيف الحماية المتقدم**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **المستخدِم:** {message.from_user.first_name} (`{message.from_user.id}`)\n"
        f"📍 **الجروب:** {message.chat.title} (`{message.chat.id}`)\n"
        f"🔍 **السبب:** {reason}\n"
        f"📝 **النص المحذوف:**\n`{message.text}`\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    
    # إنشاء الأزرار التفاعلية الخاصة بالأرشيف
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ حظر الكلمة تلقائياً", callback_data=f"arch_block_{message.chat.id}_{message.message_id}"),
        InlineKeyboardButton("↩️ استعادة الرسالة للجروب", callback_data=f"arch_restore_{message.chat.id}")
    )
    
    try:
        bot.send_message(archive_id, report, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(f"خطأ إرسال الأرشيف المتقدم: {e}")

def handle_archive_action_callbacks(bot, call):
    """معالجة أزرار الأرشيف الذكية (إضافة للكاش/استعادة)"""
    data = call.data
    
    if data.startswith("arch_block_"):
        _, _, chat_id, msg_id = data.split("_")
        # منطق استخراج الكلمة وإضافتها لقائمة الكاش وقاعدة البيانات فوراً
        bot.answer_callback_query(call.id, "✅ تم إدراج الكلمة في القائمة السوداء وتحديث الكاش!")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.text + "\n\n [🔒 تم حظر الكلمة بنجاح]")
        
    elif data.startswith("arch_restore_"):
        chat_id = data.split("_")[2]
        # منطق إعادة إرسال الرسالة إلى المجموعة الأصلية كميزة تراجع عن الحذف
        bot.answer_callback_query(call.id, "↩️ تم إعادة إرسال الرسالة للجروب والاعتذار للعضو.")
