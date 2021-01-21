"""
Copyright 2021 Douglas Myers-Turnbull

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. See the License for the specific language governing
permissions and limitations under the License.

Code that maps Windows timezones.
"""

from __future__ import annotations
from datetime import datetime, timezone
import logging
import time
from pathlib import Path
from typing import Optional, FrozenSet, KeysView
from zoneinfo import ZoneInfo

from ensuretimezone._model import TaggedDatetime, TaggedInterval
from ensuretimezone._cache import TimezoneMapFilesysCache, TimezoneMapBackend

logger = logging.getLogger("ensuretimezone")
empty_frozenset = frozenset([])


class TimezoneMap:

    @classmethod
    def cached(
        cls, path: Path = Path.home() / ".timezone-map.json", expiration_mins: int = 43830
    ) -> TimezoneMap:
        return TimezoneMap(TimezoneMapFilesysCache(path, expiration_mins))

    @classmethod
    def non_cached(cls) -> TimezoneMap:
        return TimezoneMap(TimezoneMapFilesysCache(None))

    def __init__(self, cache: TimezoneMapBackend):
        self._cache = cache
        self._map = None

    def all_zones(self) -> KeysView[str]:
        return self._map.keys()

    def tagged_interval(self, start: TaggedDatetime, end: TaggedDatetime) -> TaggedInterval:
        return TaggedInterval(start, end)

    def tagged_now(self) -> TaggedDatetime:
        t1 = time.monotonic_ns()
        dt = datetime.now(timezone.utc).astimezone()
        tz = dt.tzinfo.tzname(dt)
        iana = self.primary_zone(tz)
        return TaggedDatetime(dt, iana, tz, t1)

    def tagged_local_datetime(self, local: datetime) -> TaggedDatetime:
        t1 = time.monotonic_ns()
        if local.tzinfo is not None:
            raise ValueError(f"Datetime {local} already has a timezone {local.tzinfo}")
        dt = local.astimezone()
        tz = dt.tzinfo.tzname(dt)
        iana = self.primary_zone(tz)
        return TaggedDatetime(dt, iana, tz, t1)

    def local_primary_zone(self) -> ZoneInfo:
        dt = datetime.now(timezone.utc).astimezone()
        tz = dt.tzinfo.tzname(dt)
        return self.primary_zone(tz)

    def primary_zone(self, zone: str) -> ZoneInfo:
        match = self.get_primary_zone(zone)
        if match is None:
            raise KeyError(f"Timezone '{zone}' could not be mapped to a primary IANA timezone")
        return match

    def get_primary_zone(self, zone: str) -> Optional[ZoneInfo]:
        self._ensure()
        return self._map.get(zone, {}).get("001", empty_frozenset)

    def get_zones_with_territory(self, zone: str, territory: Optional[str]) -> FrozenSet[ZoneInfo]:
        self._ensure()
        return self._map.get(zone, {}).get(territory, empty_frozenset)

    def _ensure(self) -> None:
        if self._map is None:
            self._map = self._cache.get()


if __name__ == "__main__":
    z = TimezoneMap.non_cached()
    print(z.tagged_now())


__all__ = ["TimezoneMap"]
