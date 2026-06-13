"""
حالات المحادثة (FSM States) لنظام الخصم والمكافأة.

التدفق:
1. رد + "خصم"/"مكافأة" -> تظهر أزرار المبلغ (لا حالة بعد)
2. اختيار مبلغ -> الحالة تصبح waiting_reason
3. كتابة السبب (أو ضغط "بدون سبب") -> تظهر أزرار التأكيد
4. التأكيد -> تنفيذ العملية وتنتهي الحالة
"""

from aiogram.fsm.state import State, StatesGroup


class RewardStates(StatesGroup):
    waiting_reason = State()
