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
