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
from typing import Optional, FrozenSet
from zoneinfo import ZoneInfo
from copy import deepcopy

from suretime._model import (
    TaggedDatetime,
    TaggedInterval,
    TzMapType,
    GenericTimezone,
    DatetimeHasZoneError,
    MappedTzNotFoundError,
    MappedTzNotUniqueError,
    CannotMapTzError,
    DatetimeMissingZoneError,
    ExactTimezone,
)
from suretime._cache import TimezoneMapFilesysCache, TimezoneMapBackend

logger = logging.getLogger("suretime")
empty_frozenset = frozenset([])


class Zones:
    def __init__(self, mp):
        self._map = mp

    def list(self) -> FrozenSet[str]:
        return frozenset(sorted(self._map.keys()))

    def only_local(self, territory: Optional[str] = "primary") -> ZoneInfo:
        dt = datetime.now(timezone.utc).astimezone()
        tz = dt.tzinfo.tzname(dt)
        return self.only(tz, territory)

    def first_local(self, territory: Optional[str] = "primary") -> ZoneInfo:
        dt = datetime.now(timezone.utc).astimezone()
        tz = dt.tzinfo.tzname(dt)
        return self.first(tz, territory)

    def first(self, zone: str, territory: Optional[str] = "primary") -> Optional[ZoneInfo]:
        matches = self.all(zone, territory)
        return next(iter(matches))

    def only(self, zone: str, territory: Optional[str] = "primary") -> Optional[ZoneInfo]:
        matches = self.all(zone, territory)
        if len(matches) == 0:
            raise MappedTzNotFoundError(
                f"{len(matches)} IANA zones for zone {zone}, territory {territory}"
            )
        if len(matches) > 1:
            raise MappedTzNotUniqueError(
                f"{len(matches)} IANA zones for zone {zone}, territory {territory}"
            )
        return next(iter(matches))

    def all(self, zone: str, territory: Optional[str] = "primary") -> FrozenSet[ZoneInfo]:
        if territory is None or territory == "primary":
            territory = "001"
        matches = self._map.get(zone, {}).get(territory, empty_frozenset)
        return frozenset(sorted(matches))


class Tagged:
    def __init__(self, zones: Zones):
        self._zones = zones

    def interval(self, start: TaggedDatetime, end: TaggedDatetime) -> TaggedInterval:
        return TaggedInterval(start, end)

    def now(self, territory: Optional[str] = "primary", only: bool = True) -> TaggedDatetime:
        local = datetime.now(timezone.utc).astimezone()
        return self._get(local, territory, only=only)

    def local(
        self, local: datetime, territory: Optional[str] = "primary", only: bool = True
    ) -> TaggedDatetime:
        if local.tzinfo is not None:
            raise DatetimeHasZoneError(f"Datetime {local} already has a timezone {local.tzinfo}")
        return self._get(local, territory, only=only)

    def exact(self, zoned: datetime) -> TaggedDatetime:
        t1 = time.monotonic_ns()
        info = ZoneInfo(zoned.tzinfo.tzname(zoned))
        if info is None:
            raise DatetimeMissingZoneError(f"Datetime {zoned} is missing a zone")
        source = GenericTimezone(str(info), None, frozenset({info}))
        return TaggedDatetime(zoned, info, source, t1)

    def _get(self, local: datetime, territory: Optional[str], only: bool):
        t1 = time.monotonic_ns()
        dt = local.astimezone()
        tz = dt.tzinfo.tzname(dt)
        matches = self._zones.all(tz, territory)
        if only:
            iana = self._zones.only(tz, territory)
        else:
            iana = self._zones.first(tz, territory)
        original = GenericTimezone(tz, territory, matches)
        return TaggedDatetime(dt, iana, original, t1)


class Types:
    TaggedDatetime = TaggedDatetime
    TaggedInterval = TaggedInterval
    GenericTimezone = GenericTimezone
    ExactTimezone = ExactTimezone
    CannotMapTzError = CannotMapTzError
    DatetimeAlreadyHasZoneError = DatetimeHasZoneError
    MappedTzNotFoundError = MappedTzNotFoundError
    MappedTzNotUniqueError = MappedTzNotUniqueError


class TimezoneMap:
    def __init__(self, cache: TimezoneMapBackend, use_system: bool = False):
        self._cache = cache
        self._map = None
        self._use_system = use_system

    Types = Types

    def mapping(self) -> TzMapType:
        self._ensure()
        return deepcopy(self._map)

    @property
    def zones(self) -> Zones:
        self._ensure()
        return Zones(self._map)

    @property
    def tagged(self) -> Tagged:
        self._ensure()
        return Tagged(self.zones)

    def _ensure(self) -> None:
        if self._map is None:
            self._map = self._cache.get()


class TimezoneMaps:
    @classmethod
    def cached(
        cls,
        path: Path = Path.home() / ".timezone-map.json",
        expiration_mins: int = 43830,
    ) -> TimezoneMap:
        return TimezoneMap(TimezoneMapFilesysCache(path, expiration_mins))

    @classmethod
    def non_cached(cls) -> TimezoneMap:
        return TimezoneMap(TimezoneMapFilesysCache(None))


if __name__ == "__main__":
    my_zone = TimezoneMaps.non_cached()
    print(my_zone.tagged.now(only=False))


__all__ = ["TimezoneMap", "TimezoneMaps"]
