from aiogram import Router, html, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.user_state import UserState
from handlers.main_buttons_handlers import change_group

# from rusoil_api.rusoil_baseapi import RusoilAPI
from rusoil_api.rusoil_cachingapi import RusoilSafeAPI
from keyboards.main_menu import main_menu


router = Router()

async def update_group(message: Message, state: FSMContext, group_name: str):
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
async def find_group(message: Message, state: FSMContext, api: RusoilSafeAPI):
    if not message.text:
        return
    group_name = message.text.strip()

    if len(group_name) < 2:
        await message.answer("Слишком короткое название группы.")
        return

    try:
        groups, _ = await api.GetGroups(group_name) # api.get_groups(group_name)
    except:
        await message.answer("Произошла ошибка. Попробуй еще раз")
        return

    if not groups:
        await message.answer("Группа не найдена. Попробуй еще раз")
        return

    exact = next((g for g in groups if g.name.lower() == group_name.lower()), None)
    if exact:
        await update_group(message, state, exact.name)
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
        "Выбери свою группу:",
        reply_markup=keyboard
    )
    await state.set_state(UserState.waiting_for_group_choice)

@router.callback_query(UserState.waiting_for_group_choice, F.data.startswith("group:"))
async def process_group_choice(callback: CallbackQuery, state: FSMContext):
    if not callback.data or not isinstance(callback.message, Message):
        return

    group_name = callback.data.split(":", 1)[1]

    if group_name == "cancel":
        await change_group(callback.message, state)
        await callback.message.delete()
        return

    await update_group(callback.message, state, group_name)

    await callback.answer()  # убрать "часики" на кнопке
    await callback.message.delete()


@router.callback_query(UserState.waiting_subgroup, F.data.startswith("subgroup:"))
async def process_subgroup_choice(callback: CallbackQuery, state: FSMContext):
    if not callback.data or not isinstance(callback.message, Message):
        return

    subgroup_num = int(callback.data.split(":", 1)[1])
    await callback.answer()
    await state.update_data(subgroup = subgroup_num)

    data = await state.get_data()

    await callback.message.answer(F"Я запомнил. Твоя группа - {html.bold(data['group'])}, а подгруппа - {html.bold(str(subgroup_num))}", reply_markup=main_menu)

    await callback.message.delete()