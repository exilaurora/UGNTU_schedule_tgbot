import aiohttp
import asyncio
from typing import List, Optional
from dataclasses import dataclass, field
from itertools import groupby


# ========================
#  Кастомные исключения
# ========================

class RusoilAPIError(Exception):
    """Базовая ошибка клиента Rusoil API"""
    pass


class RusoilServerError(RusoilAPIError):
    """Ошибка при обращении к серверу (недоступен, 5xx и т.д.)"""
    pass


class RusoilInvalidResponse(RusoilAPIError):
    """Сервер вернул неожидаемый ответ"""
    pass


# ========================
#  Модели данных
# ========================

@dataclass
class Group:
    id: int
    filial: int
    name: str
    bellfak: int
    fob: int

    @classmethod
    def from_dict(cls, data: dict) -> "Group":
        return cls(
            id=int(data.get("id", 0)),
            filial=int(data.get("FILIAL", 0)),
            name=str(data.get("GRUPPA", "")),
            bellfak=int(data.get("BELLFAK", 0)),
            fob=int(data.get("FOB", 0)),
        )


@dataclass
class Lesson:
    dayweek: int
    para: int
    beginweek: int
    endweek: int
    discipline: str
    teacher: str
    audience: str
    start_time: str
    end_time: str
    lesson_type: str
    subgroup: str

    @classmethod
    def from_dict(cls, data: dict) -> "Lesson":
        return cls(
            dayweek=int(data.get("DAYWEEK", 0)),
            para=int(data.get("PARA", 0)),
            beginweek=int(data.get("BEGINWEEK", 0)),
            endweek=int(data.get("ENDWEEK", 0)),
            discipline=str(data.get("NDISC", "")),
            teacher=str(data.get("TEACHER_NAME", "")),
            audience=str(data.get("AUD", "")),
            start_time=str(data.get("START_TIME", "")),
            end_time=str(data.get("END_TIME", "")),
            lesson_type=str(data.get("NVIDZANAT", "")),
            subgroup=str(data.get("PODGRUPPA", "")),
        )


@dataclass
class Day:
    day_of_week: int
    date: Optional[str] = None
    lessons: List[Lesson] = field(default_factory=list)

    def __repr__(self):
        day_names = {
            1: "Понедельник",
            2: "Вторник",
            3: "Среда",
            4: "Четверг",
            5: "Пятница",
            6: "Суббота",
            7: "Воскресенье",
        }
        name = day_names.get(self.day_of_week, f"День {self.day_of_week}")
        return f"<{name}: {len(self.lessons)} пар>"


@dataclass
class NowInfo:
    """Текущая неделя и день недели"""
    week_number: int
    day_of_week: int

    @classmethod
    def from_dict(cls, data: dict) -> "NowInfo":
        return cls(
            week_number=int(data.get("NUMWEEK", 0)),
            day_of_week=int(data.get("DAYWEEK", 0))
        )


# ========================
#  Клиент API
# ========================

class RusoilAPI:
    BASE_URL = "https://raspisanie.rusoil.net/origins"

    def __init__(self, timeout: float = 10.0):
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def _post(self, endpoint: str, payload: dict) -> dict:
        """Универсальный метод запроса с обработкой ошибок"""
        if not self.session:
            raise RusoilAPIError("Session not initialized. Use 'async with RusoilAPI()'.")

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            async with self.session.post(url, json=payload) as r:
                if r.status >= 500:
                    raise RusoilServerError(f"Server error {r.status} at {url}")
                if r.status >= 400:
                    raise RusoilAPIError(f"Client error {r.status} at {url}")

                try:
                    return await r.json(content_type=None)
                except Exception as e:
                    text = await r.text()
                    raise RusoilInvalidResponse(f"Invalid JSON: {e}. Response: {text[:200]}")

        except asyncio.TimeoutError:
            raise RusoilServerError(f"Request to {url} timed out.")
        except aiohttp.ClientError as e:
            raise RusoilServerError(f"Network error while requesting {url}: {e}")

    async def get_groups(self, search: str, id_fak: int = 0) -> List[Group]:
        data = await self._post("get_groups", {"id_fak": id_fak, "search": search})
        groups_data = data.get("groups")
        if not groups_data:  # None, [], или пустое значение
            return []

        if not isinstance(groups_data, list):
            raise RusoilInvalidResponse(f"Expected list for 'groups', got: {type(groups_data)}")

        if "groups" not in data:
            raise RusoilInvalidResponse(f"Unexpected response: {data}")
        return [Group.from_dict(g) for g in data["groups"]]

    async def get_schedule(self, group: str, beginweek: int) -> List[Day]:
        lessons_data = await self._post(
            "get_rasp_student",
            {"gruppa": group, "beginweek": beginweek, "endweek": beginweek},
        )

        if not isinstance(lessons_data, list):
            raise RusoilInvalidResponse(f"Expected list of lessons, got: {type(lessons_data)}")

        lessons = [Lesson.from_dict(l) for l in lessons_data]

        # группируем по дню недели
        days: List[Day] = []
        for day_of_week, group_iter in groupby(sorted(lessons, key=lambda x: x.dayweek), key=lambda x: x.dayweek):
            days.append(Day(day_of_week=day_of_week, lessons=list(group_iter)))
        return days

    async def get_now(self) -> NowInfo:
        """Возвращает текущую неделю и день недели"""
        data = await self._post("get_now", {})

        if "now" not in data or not isinstance(data["now"], list) or not data["now"]:
            raise RusoilInvalidResponse(f"Unexpected response: {data}")

        return NowInfo.from_dict(data["now"][0])