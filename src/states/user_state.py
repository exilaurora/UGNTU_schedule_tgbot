from aiogram.fsm.state import StatesGroup, State

class UserState(StatesGroup):
    waiting_for_group = State()
    waiting_for_group_choice = State()
    waiting_subgroup = State()
    group_configured = State()