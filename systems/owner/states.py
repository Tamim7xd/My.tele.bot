"""
حالات المحادثة (FSM States) لـ لوحة التحكم.

تُستخدم عند تعديل قيم الإعدادات (مثل قيم الخصم/المكافأة،
أو عدد رسائل التنظيف) من اللوحة.
"""

from aiogram.fsm.state import State, StatesGroup

class OwnerStates(StatesGroup):
    # انتظار إدخال قيم جديدة للخصم/المكافأة (4 أرقام مفصولة بفواصل)
    waiting_reward_amounts = State()

    # انتظار إدخال عدد جديد لرسائل التنظيف
    waiting_cleanup_range = State()

    # انتظار إدخال قيمة جديدة تُضاف لقائمة قيم الخصم/المكافأة
    waiting_new_reward_amount = State()

    # انتظار إدخال رصيد جديد لعضو معين (تعديل مباشر)
    waiting_member_balance = State()

    # انتظار نص البحث عن عضو
    waiting_member_search = State()

    # انتظار إدخال مستوى جديد لعضو معين (تعديل مباشر)
    waiting_member_level = State()

    # انتظار إدخال قيمة جديدة لإعدادات المستويات
    waiting_levels_tier1 = State()
    waiting_levels_tier2 = State()
    waiting_levels_reward = State()

    # انتظار نص البحث عن عضو في قائمة الأرشيف المستقلة
    waiting_archive_search = State()

    # نظام الإعلانات (announcements)
    waiting_announcement_trigger = State()
    waiting_announcement_text = State()
    waiting_announcement_edit_text = State()

    # نظام الحماية (protection)
    waiting_protection_word = State()

    # ═══════════════════════════════════════
    # ═══ نظام العضويات الإدارية ═══
    # ═══════════════════════════════════════
    
    # ─── إضافة عضوية جديدة ───
    waiting_rank_name = State()          # الاسم التقني
    waiting_rank_display = State()       # الاسم المعروض
    waiting_rank_level = State()         # المستوى الهرمي
    waiting_rank_color = State()         # اللون
    waiting_rank_icon = State()          # الأيقونة
    waiting_rank_permissions = State()   # الصلاحيات
    
    # ─── تعديل عضوية ───
    waiting_rank_edit_name = State()     # تعديل الاسم
    waiting_rank_edit_color = State()    # تعديل اللون
    waiting_rank_edit_icon = State()     # تعديل الأيقونة
