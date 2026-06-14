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
