from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from states.user_state import UserState
from aiogram.fsm.context import FSMContext
from .main_buttons_handlers import get_now_safe, get_schedule_safe, render_schedule_text, days_names
from rusoil_api import NowInfo, RusoilAPI

router = Router()

@router.inline_query()
async def inline_query_handler(query: InlineQuery, state: FSMContext, api: RusoilAPI):
    text = query.query.strip()
    if not text:
        return
    
    # query.from_user

    results = []

    data = await state.get_data()
    if data.get("group"):
        group = data["group"]
        subgroup = data.get("subgroup", 0)
        now, now_cache = await get_now_safe(api)

        if not now:
            query.answer(results, cache_time=60, is_personal=True)
            return
        
        days, days_from_cache = await get_schedule_safe(api, group, now.week_number)

        if not days:
            query.answer(results, cache_time=60, is_personal=True)
            return

        today_obj = next((d for d in days if d.day_of_week == now.day_of_week), None)

        todayRaspText = render_schedule_text(group, today_obj, days_names[now.day_of_week], subgroup, True if days_from_cache or now_cache else False)


        tommorow_obj = next((d for d in days if d.day_of_week == (now.day_of_week + 1 if now.day_of_week < 7 else 1)), None)

        tommorowRaspText = render_schedule_text(group, tommorow_obj, days_names[now.day_of_week + 1 if now.day_of_week < 7 else 1], subgroup, True if days_from_cache or now_cache else False)


        results.append(InlineQueryResultArticle(
            id = "1",
            title = f"Расписание на сегодня для {group}",
            input_message_content = InputTextMessageContent(
                message_text=todayRaspText
            ),
            description = "Вывести расписание на сегодня"
            )
        )
        results.append(InlineQueryResultArticle(
            id = "2",
            title = f"Расписание на завтра для {group}",
            input_message_content = InputTextMessageContent(
                message_text=tommorowRaspText
            ),
            description = "Вывести расписание на завтра"
            )
        )

    await query.answer(results, cache_time=60, is_personal=True)