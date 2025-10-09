from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📅 Расписание на сегодня"),
            # KeyboardButton(text="📆 Расписание на неделю")
        ],
        [
            KeyboardButton(text="🔄 Сменить группу")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие..."
)