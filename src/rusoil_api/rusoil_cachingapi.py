from typing import List
import rusoil_api.rusoil_baseapi as API
from time import time

class RusoilSafeAPI(API.RusoilAPI):
    groupCache: dict[tuple[str, int], dict] = {}
    findCache: dict[str, dict] = {}
    nowCache: dict = {"data": None, "time": 0}

    async def GetGroups(self, search: str, id_fak: int = 0, cache_ttl: int = 60) -> tuple[List[API.Group], bool]:
        entry = self.findCache.get(search)

        curTime = time()

        if entry and curTime - entry["time"] < cache_ttl:
            return entry["data"], False
        
        try:
            data = await self.get_groups(search, id_fak)
            self.findCache[search] = {"time" : curTime, "data": data}
            return data, False
        except Exception as e:
            if entry:
                return entry["data"], True
            raise(e)
        
    async def GetSchedule(self, group: str, week: int, cache_ttl: int = 60) -> tuple[List[API.Day], bool]:
        key = (group, week)
        entry = self.groupCache.get(key)

        curTime = time()

        if entry and curTime - entry["time"] < cache_ttl:
            return entry["data"], False
        
        try:
            data = await self.get_schedule(group, week, week)
            self.groupCache[key] = {"time": curTime, "data": data}
            return data, False
        except Exception as e:
            if entry:
                return entry["data"]
            raise(e)
        
    async def GetNow(self, cache_ttl: int = 60) -> tuple[API.NowInfo, bool]:
        entry = self.nowCache

        curTime = time()

        if curTime - entry["time"] < cache_ttl:
            return entry["data"], False
        
        try:
            data = await self.get_now()
            self.nowCache = {"time": curTime, "data": data}
            return data, False
        except Exception as e:
            if entry["data"]:
                return entry["data"]
            raise e