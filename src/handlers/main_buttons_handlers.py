import json
import time
import logging
from typing import Optional

from aiogram import Router, html, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from filters.has_group import HasGroupFilter
from filters.is_today_schedule import IsTodaySchedule
from filters.is_changing_group import IsChangingGroup
from rusoil_api import RusoilAPI, NowInfo
from states.user_state import UserState


router = Router()

# === Конфигурация ===
CACHE_TTL = 60.0  # секунды
cache: dict[tuple[str, int], dict] = {}
now_cache: dict = {"data": None, "time": 0}

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

async def get_now_safe(api: RusoilAPI) -> tuple[Optional[NowInfo], bool]:
    global now_cache
    now_ts = time.time()

    if now_cache["data"] and now_ts - now_cache["time"] < CACHE_TTL:
        logging.info("[CACHE] Используем кэш now_cache")
        return now_cache["data"], False

    try:
        now = await api.get_now()
        now_cache["data"] = now
        now_cache["time"] = now_ts
        logging.info("[CACHE] Обновлен now_cache")
        return now, False
    except Exception as e:
        logging.warning(f"[WARN] API недоступен: {e}")
        if now_cache["data"]:
            logging.info(f"[CACHE] Используем просроченные данные для now_cache")
            return now_cache["data"], True
        return None, True


async def get_schedule_safe(api: RusoilAPI, group: str, week: int) -> tuple[Optional[list], bool]:
    """
    Безопасное получение расписания с кэшем и TTL.
    Возвращает данные из кэша, если прошло < CACHE_TTL секунд.
    """
    cache_key = (group, week)
    entry = cache.get(cache_key)

    # проверка на актуальность
    if entry and time.time() - entry["time"] < CACHE_TTL:
        logging.info(f"[CACHE] Используем кэш: {cache_key}")
        return entry["days"], False

    # иначе пробуем запросить с API
    try:
        days = await api.get_schedule(group, week)
        cache[cache_key] = {"days": days, "time": time.time()}
        logging.info(f"[CACHE] Обновлено: {cache_key}")
        return days, False
    except Exception as e:
        logging.warning(f"[WARN] API недоступен: {e}")
        # если есть хоть что-то старое — используем
        if entry:
            logging.info(f"[CACHE] Используем просроченные данные: {cache_key}")
            return entry["days"], True
        return None, True


def render_schedule_text(group: str, day_obj, day_name: str, subgroup: int, from_cache: bool = False) -> str:
    if not day_obj or not day_obj.lessons:
        return f"📅 Расписание на {day_name} ({group}):\n\n" \
               f"Пар нет 🎉 {html.spoiler('наверное')}"

    lines = []
    if from_cache:
        lines.append("⚠️ API УГНТУ не доступен. Используются данные из кэша\n")

    lines.append(f"📅 Расписание на {day_name} ({group}):\n")

    for les in day_obj.lessons:
        if les.subgroup and int(les.subgroup) != subgroup:
            continue

        subgroup_text = f"  👥 Подгруппа: {les.subgroup}\n" if les.subgroup else ""
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

@router.message(IsTodaySchedule(), HasGroupFilter())
async def schedule_today(message: Message, state: FSMContext, api: RusoilAPI):
    now, now_from_cache = await get_now_safe(api)
    if not now:
        await message.reply("⚠️ Не удалось получить текущую дату, и кэш пуст.")
        return

    data = await state.get_data()
    group = data["group"]
    subgroup = data.get("subgroup", 0)

    days, days_from_cache = await get_schedule_safe(api, group, now.week_number)
    if not days:
        await message.reply("⚠️ Не удалось получить расписание, и кэш пуст.")
        return

    today_obj = next((d for d in days if d.day_of_week == now.day_of_week), None)
    text = render_schedule_text(group, today_obj, days_names[now.day_of_week], subgroup, True if now_from_cache or days_from_cache else False)
    await message.answer(text, reply_markup=make_day_keyboard(now.week_number, now.day_of_week, group, subgroup))


@router.callback_query(F.data.startswith("dw:"), HasGroupFilter())
async def change_day(callback: CallbackQuery, state: FSMContext, api: RusoilAPI):
    if not callback.data or not isinstance(callback.message, Message):
        return

    message = callback.message
    day_data = json.loads(callback.data[3:])
    state_data = await state.get_data()
    group = state_data["group"] if day_data.get("g") is None else day_data["g"]
    subgroup = state_data.get("subgroup", 0) if day_data.get("s") is None else day_data["s"]

    now_from_cache = False

    if day_data["w"] == -1 and day_data["d"] == -1:
        now, now_from_cache = await get_now_safe(api)
        if not now:
            await message.answer("⚠️ Не удалось получить текущий день, и кэш пуст.")
            return
        day_data.update({"w": now.week_number, "d": now.day_of_week})

    days, days_from_cache = await get_schedule_safe(api, group, day_data["w"])
    if not days:
        await message.reply("⚠️ Не удалось получить расписание, и кэш пуст.")
        return

    today_obj = next((d for d in days if d.day_of_week == day_data["d"]), None)
    text = render_schedule_text(group, today_obj, days_names[day_data["d"]], subgroup, True if now_from_cache or days_from_cache else False)
    try:
        await message.edit_text(text, reply_markup=make_day_keyboard(day_data["w"], day_data["d"], group, subgroup))
    except TelegramBadRequest as e:
        pass
    await callback.answer()


@router.message(IsChangingGroup())
async def change_group(message: Message, state: FSMContext):
    await message.answer("Введи свою группу", reply_markup=ReplyKeyboardRemove())
    await state.clear()
    await state.set_state(UserState.waiting_for_group)