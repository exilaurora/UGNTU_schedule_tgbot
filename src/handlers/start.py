from aiogram import Router, html, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from rusoil_api import RusoilAPI
from states.user_state import UserState
from keyboards.main_menu import main_menu

from handlers.main_buttons_handlers import change_group

router = Router()

@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    user = message.from_user
    if not user:
        return

    await message.answer("Привет! Введи свою группу", reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserState.waiting_for_group)

async def update_group(message: Message, state: FSMContext, api: RusoilAPI, group_name: str):
    # await message.answer(f"✅ Группа {html.bold(group_name)} найдена и сохранена!")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1", callback_data="subgroup:1"),
                InlineKeyboardButton(text="2", callback_data="subgroup:2")
            ]
        ]
    )
    await message.answer(f"Укажи свою подгруппу", reply_markup=keyboard)

    await state.update_data(group=group_name)
    await state.set_state(UserState.waiting_subgroup)



@router.message(UserState.waiting_for_group)
async def find_group(message: Message, state: FSMContext, api: RusoilAPI):
    if not message.text:
        return
    group_name = message.text.strip()

    groups = await api.get_groups(group_name)

    if not groups:
        await message.answer("Группа не найдена. Попробуй еще раз")
        # await message.reply("Введи свою группу")
        return

    exact = next((g for g in groups if g.name.lower() == group_name.lower()), None)
    if exact:
        await update_group(message, state, api, exact.name)
        return

    rows = []
    for i in range(0, len(groups[:18]), 2):
        row = []
        for g in groups[i:i+2]:
            row.append(InlineKeyboardButton(text=g.name, callback_data=f"group:{g.name}"))
        rows.append(row)

    rows.append([InlineKeyboardButton(text="Отменить", callback_data="group:cancel")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)


    await message.answer(
        "Выберите свою группу:",
        reply_markup=keyboard
    )
    await state.set_state(UserState.waiting_for_group_choice)

@router.callback_query(UserState.waiting_for_group_choice, F.data.startswith("group:"))
async def process_group_choice(callback: CallbackQuery, state: FSMContext, api: RusoilAPI):
    if not callback.data or not isinstance(callback.message, Message):
        return

    group_name = callback.data.split(":", 1)[1]

    if group_name == "cancel":
        await change_group(callback.message, state)
        await callback.message.delete()
        return

    await update_group(callback.message, state, api, group_name)

    await callback.answer()  # убрать "часики" на кнопке
    await callback.message.delete()


@router.callback_query(UserState.waiting_subgroup, F.data.startswith("subgroup:"))
async def process_subgroup_choice(callback: CallbackQuery, state: FSMContext, api: RusoilAPI):
    if not callback.data or not isinstance(callback.message, Message):
        return

    subgroup_num = int(callback.data.split(":", 1)[1])
    await callback.answer()
    await state.update_data(subgroup = subgroup_num)

    data = await state.get_data()

    await callback.message.answer(F"Я запомнил. Твоя группа - {html.bold(data['group'])}, а подгруппа - {html.bold(str(subgroup_num))}", reply_markup=main_menu)

    await callback.message.delete()