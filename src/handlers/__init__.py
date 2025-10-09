from aiogram import Dispatcher
from . import start, schedule, main_buttons_handlers, test

def register_handlers(dp: Dispatcher):
    """
    Регистрирует все роутеры бота.
    """
    dp.include_router(start.router)
    dp.include_router(schedule.router)
    dp.include_router(main_buttons_handlers.router)
    dp.include_router(test.router)