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

    # نظام الألعاب (games)
    waiting_games_cooldown = State()
    waiting_trivia_question = State()
    waiting_trivia_answers = State()
    waiting_trivia_reward = State()
    waiting_trivia_timeout = State()
    waiting_riddle_question = State()
    waiting_riddle_answers = State()
    waiting_riddle_reward = State()
    waiting_riddles_timeout = State()
    waiting_rps_reward = State()
    waiting_lucky_box_fee = State()
    waiting_lucky_box_outcome_amount = State()
    waiting_lucky_box_outcome_weight = State()
    waiting_ls_fee = State()
    waiting_ls_join_window = State()
    waiting_ls_min_players = State()
    waiting_ls_elimination_delay = State()

    # نظام المتجر (shop)
    waiting_membership_name = State()
    waiting_membership_price = State()
    waiting_membership_duration_value = State()
    waiting_membership_daily_reward = State()
    waiting_title_name = State()
    waiting_title_price = State()
    waiting_clear_chat_price = State()
    waiting_clear_chat_range = State()
    waiting_member_membership_extend = State()

    # خيارات النظام (protection - system words)
    waiting_protection_system_word = State()

    # نظام التحويل (transfer)
    waiting_transfer_min = State()
    waiting_transfer_max = State()
    waiting_transfer_fee = State()

    # مكافأة/خصم جماعي
    waiting_bulk_reward_amount = State()
    waiting_bulk_deduct_amount = State()
