import json

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from filters.group_configured import GroupConfigured
from rusoil_api.rusoil_cachingapi import RusoilSafeAPI
from states.user_state import UserState


router = Router()

# === Конфигурация ===

days_names = {
    1: "Понедельник",
    2: "Вторник",
    3: "Среду",
    4: "Четверг",
    5: "Пятницу",
    6: "Субботу",
    7: "Воскресенье"
}

# === Утилиты ===
def render_schedule_text(group: str, day_obj, day_name: str, subgroup: int, from_cache: bool = False) -> str:
    lines = []
    if from_cache:
        lines.append("⚠️ API УГНТУ не доступен. Используются данные из кэша\n")

    lines.append(f"📅 Расписание на {day_name} ({group}):\n")

    if not day_obj or not day_obj.lessons:
        lines.append("Пар нет 🎉")
        return "\n".join(lines)

    for les in day_obj.lessons:
        if subgroup != -1 and les.subgroup and int(les.subgroup) != subgroup and int(les.subgroup) < 2:
            continue

        subgroup_text = f"  👥 Подгруппа: {les.subgroup}\n" if les.subgroup and int(les.subgroup) <= 2 else ""
        lines.append(
            f"[{les.para} пара] {les.lesson_type}\n"
            f"  📘 {les.discipline}\n"
            f"  🕒 {les.start_time[:-3]}–{les.end_time[:-3]}\n"
            f"  👩‍🏫 {les.teacher}\n"
            f"  🏫 {les.audience}\n"
            f"{subgroup_text}"
            # f"  💬 {les.lesson_type}\n"
        )

    return "\n".join(lines)


def make_day_keyboard(week: int, day: int, group: str, subgroup: int) -> InlineKeyboardMarkup:
    today_data = json.dumps({"w": -1, "d": -1, "g": group, "s": subgroup})
    tomorrow_data = json.dumps({"w": week + 1, "d": 1, "g": group, "s": subgroup}) if day == 7 else json.dumps({"w": week, "d": day + 1, "g": group, "s": subgroup})
    yesterday_data = json.dumps({"w": max(1, week - 1), "d": 7, "g": group, "s": subgroup}) if day == 1 else json.dumps({"w": week, "d": day - 1, "g": group, "s": subgroup})

    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="<", callback_data=f"dw:{yesterday_data}"),
            InlineKeyboardButton(text="Сегодня", callback_data=f"dw:{today_data}"),
            InlineKeyboardButton(text=">", callback_data=f"dw:{tomorrow_data}"),
        ]]
    )

# === Хэндлеры ===

@router.message(GroupConfigured(), lambda message: message.text == "📅 Расписание на сегодня")
async def schedule_today(message: Message, state: FSMContext, api: RusoilSafeAPI):
    try:
        now, now_from_cache = await api.GetNow() # get_now_safe(api)
    except:
        await message.reply("⚠️ Не удалось получить текущую дату, и кэш пуст.")
        return

    data = await state.get_data()
    group = data["group"]
    subgroup = data.get("subgroup", 0)

    try:
        days, days_from_cache = await api.GetSchedule(group, now.week_number) # get_schedule_safe(api, group, now.week_number)
    except:
        await message.reply("⚠️ Не удалось получить расписание, и кэш пуст.")
        return

    today_obj = next((d for d in days if d.day_of_week == now.day_of_week), None)
    text = render_schedule_text(group, today_obj, days_names[now.day_of_week], subgroup, True if now_from_cache or days_from_cache else False)
    await message.answer(text, reply_markup=make_day_keyboard(now.week_number, now.day_of_week, group, subgroup))


@router.callback_query(F.data.startswith("dw:"), GroupConfigured())
async def change_day(callback: CallbackQuery, state: FSMContext, api: RusoilSafeAPI):
    if not callback.data or not isinstance(callback.message, Message):
        return

    message = callback.message
    day_data = json.loads(callback.data[3:])
    state_data = await state.get_data()
    group = state_data["group"] if day_data.get("g") is None else day_data["g"]
    subgroup = state_data.get("subgroup", 0) if day_data.get("s") is None else day_data["s"]

    week = day_data["w"] if day_data.get("w") is not None else day_data["week"]
    day = day_data["d"] if day_data.get("d") is not None else day_data["day"]

    now_from_cache = False

    if week == -1 and day == -1:
        try:
            now, using_cache = await api.GetNow() # get_now_safe(api)
            now_from_cache = using_cache
        except:
            await callback.answer()
            await message.answer("⚠️ Не удалось получить текущий день, и кэш пуст.")
            return
        week = now.week_number
        day = now.day_of_week
        day_data.update({"w": now.week_number, "d": now.day_of_week})

    try:
        days, days_from_cache = await api.GetSchedule(group, week) # get_schedule_safe(api, group, week)
    except:
        await callback.answer()
        await message.reply("⚠️ Не удалось получить расписание, и кэш пуст.")
        return

    today_obj = next((d for d in days if d.day_of_week == day), None)
    text = render_schedule_text(group, today_obj, days_names[day], subgroup, True if now_from_cache or days_from_cache else False)
    try:
        await message.edit_text(text, reply_markup=make_day_keyboard(week, day, group, subgroup))
    except TelegramBadRequest as e:
        pass
    await callback.answer()


@router.message(lambda message: message.text == "🔄 Сменить группу")
async def change_group(message: Message, state: FSMContext):
    await message.answer("Введи свою группу", reply_markup=ReplyKeyboardRemove())
    await state.clear()
    await state.set_state(UserState.waiting_for_group)