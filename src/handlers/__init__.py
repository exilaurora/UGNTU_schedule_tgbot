from aiogram import Dispatcher
from . import start, main_buttons_handlers, test, group_register

def register_handlers(dp: Dispatcher):
    """
    Регистрирует все роутеры бота.
    """
    dp.include_router(start.router)
    dp.include_router(main_buttons_handlers.router)
    dp.include_router(test.router)

    dp.include_router(group_register.router)