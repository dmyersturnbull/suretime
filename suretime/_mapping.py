"""
Main code for suretime.

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
from pathlib import Path
from typing import Optional, FrozenSet, Union
from zoneinfo import ZoneInfo
from copy import deepcopy

from suretime._model import (
    ZonedDatetime,
    TaggedDatetime,
    TaggedInterval,
    TzMapType,
    Duration,
    GenericTimezone,
    DatetimeHasZoneError,
    MappedTzNotFoundError,
    MappedTzNotUniqueError,
    CannotMapTzError,
    DatetimeMissingZoneError,
    InvalidIntervalError,
    DatetimeParseError,
    ExactTimezone,
)
from suretime._cache import TimezoneMapFilesysCache, TimezoneMapBackend
from suretime._utils import (
    TzUtils,
    Clock,
    ClockTime,
    ClockInfo,
    SysTzInfo,
    NtpTime,
    NtpClockType,
    NtpContinents,
)

logger = logging.getLogger("suretime")
empty_frozenset = frozenset([])


class Zones:
    def __init__(self, mp):
        self._map = mp

    def utc(self) -> ZoneInfo:
        return timezone.utc

    def list(self) -> FrozenSet[str]:
        return frozenset(sorted(self._map.keys()))

    def only_local(
        self, territory: Optional[str] = "primary", sys: bool = True, etc: bool = True
    ) -> ZoneInfo:
        dt = datetime.now(timezone.utc).astimezone()
        tz = dt.tzinfo.tzname(dt)
        only = self.only(tz, territory)
        # don't use all_local because we can avoid a system call since we only need 1 matching zone
        if only is None and sys:
            x = TzUtils.get_sys_zone()
            if x is not None:
                only = self.first(x.zone_name, territory)
        if only is None and etc:
            only = ZoneInfo(TzUtils.get_offset_zone().zone_name)
        return only

    def first_local(
        self, territory: Optional[str] = "primary", sys: bool = True, etc: bool = True
    ) -> ZoneInfo:
        dt = datetime.now(timezone.utc).astimezone()
        tz = dt.tzinfo.tzname(dt)
        first = self.first(tz, territory)
        # don't use all_local because we can avoid a system call since we only need 1 matching zone
        if first is None and sys:
            x = TzUtils.get_sys_zone()
            if x is not None:
                first = self.first(x.zone_name, territory)
        if first is None and etc:
            first = ZoneInfo(TzUtils.get_offset_zone().zone_name)
        return first

    def all_local(
        self, territory: Optional[str] = "primary", sys: bool = True, etc: bool = True
    ) -> FrozenSet[ZoneInfo]:
        dt = datetime.now(timezone.utc).astimezone()
        tz = dt.tzinfo.tzname(dt)
        matches = list(self.all(tz, territory))
        if sys:
            system = TzUtils.get_sys_zone()
            if system is not None:
                system = self.first(system.zone_name, territory)
                matches.append(system)
        if etc:
            etc_zone = ZoneInfo(TzUtils.get_offset_zone().zone_name)
            matches.append(etc_zone)
        return frozenset(matches)

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
        if territory is None or territory == "any":
            name_to_territory_map = self._map.get(zone, {})
            matches = set()
            for vals in name_to_territory_map.values():
                matches.update(vals)
            return frozenset(sorted(matches))
        if territory == "primary":
            territory = "001"
        matches = self._map.get(zone, {}).get(territory, empty_frozenset)
        return frozenset(sorted(matches))


class Tagged:
    def __init__(self, zones: Zones):
        self._zones = zones

    def interval(self, start: TaggedDatetime, end: TaggedDatetime) -> TaggedInterval:
        return TaggedInterval(start, end)

    def now_local_sys(
        self,
        territory: Optional[str] = "primary",
        only: bool = False,
        sys: bool = True,
        etc: bool = True,
    ) -> TaggedDatetime:
        return self._get_now(
            territory, only=only, sys=sys, etc=etc, ntp_server=None, ntp_clock=None
        )

    def now_local_ntp(
        self,
        territory: Optional[str] = "primary",
        only: bool = False,
        etc: bool = True,
        server: str = "europe",
        kind: Union[str, NtpClockType] = NtpClockType.client_sent,
    ) -> TaggedDatetime:
        return self._get_now(
            territory, only=only, sys=False, etc=etc, ntp_server=server, ntp_clock=kind
        )

    def now_utc_sys(self) -> TaggedDatetime:
        dt = datetime.now(timezone.utc)
        clock_time = TzUtils.get_clock_time()
        return TaggedDatetime(dt, timezone.utc, timezone.utc, clock_time.nanos, clock_time.clock)

    def now_utc_ntp(
        self,
        ntp_server: str = "europe",
        ntp_clock: Union[str, NtpClockType] = NtpClockType.client_sent,
    ) -> TaggedDatetime:
        dt = datetime.now(timezone.utc)
        clock_time = TzUtils.get_ntp_clock(ntp_server, ntp_clock)
        return TaggedDatetime(dt, timezone.utc, timezone.utc, clock_time.nanos, clock_time.clock)

    def exact(self, zoned: datetime) -> TaggedDatetime:
        clock_time = TzUtils.get_clock_time()
        info = zoned.tzinfo.tzname(zoned)
        if info is None:
            raise DatetimeMissingZoneError(f"Datetime {zoned} is missing a zone")
        info = ZoneInfo(info)
        source = GenericTimezone(str(info), None, frozenset({info}))
        return TaggedDatetime(zoned, info, source, clock_time.nanos, clock_time.clock)

    def _get(self, dt: datetime, territory: Optional[str], only: bool):
        clock_time = TzUtils.get_clock_time()
        tz = dt.tzinfo.tzname(dt)
        matches = self._zones.all(tz, territory)
        if only:
            iana = self._zones.only(tz, territory)
        else:
            iana = self._zones.first(tz, territory)
        original = GenericTimezone(tz, territory, matches)
        return TaggedDatetime(dt, iana, original, clock_time.nanos, clock_time.clock)

    def _get_now(
        self,
        territory: Optional[str],
        only: bool,
        sys: bool,
        etc: bool,
        ntp_server: Optional[str],
        ntp_clock: Optional[str],
    ):
        if ntp_server is not None:
            if ntp_clock is None:
                raise AssertionError("ntp_attribute must be non-None if ntp_server is non-None")
            clock_time = TzUtils.get_ntp_clock(ntp_server, ntp_clock)
        else:
            clock_time = TzUtils.get_clock_time()
        matches = self._zones.all_local(territory, sys=sys, etc=etc)
        if only:
            iana = self._zones.only_local(territory, sys=sys, etc=etc)
        else:
            iana = self._zones.first_local(territory, sys=sys, etc=etc)
        local_now = datetime.now(timezone.utc).astimezone()
        original = GenericTimezone(local_now.tzname(), territory, matches)
        return TaggedDatetime(local_now, iana, original, clock_time.nanos, clock_time.clock)


class Errors:
    DatetimeParseError = DatetimeParseError
    TaggedDatetime = TaggedDatetime
    TaggedInterval = TaggedInterval
    GenericTimezone = GenericTimezone
    ExactTimezone = ExactTimezone
    CannotMapTzError = CannotMapTzError
    DatetimeAlreadyHasZoneError = DatetimeHasZoneError
    MappedTzNotFoundError = MappedTzNotFoundError
    MappedTzNotUniqueError = MappedTzNotUniqueError
    InvalidIntervalError = InvalidIntervalError


class Types:
    ZonedDatetime = ZonedDatetime
    TaggedDatetime = TaggedDatetime
    TaggedInterval = TaggedInterval
    Duration = Duration
    Clock = Clock
    ClockTime = ClockTime
    ClockInfo = ClockInfo
    SysTzInfo = SysTzInfo
    NtpTime = NtpTime
    NtpClockType = NtpClockType
    NtpContinents = NtpContinents
    Utils = TzUtils


class Clocks:
    @classmethod
    def sys(cls) -> ClockTime:
        return TzUtils.get_clock_time()

    @classmethod
    def ntp(
        cls, server: str = "europe", kind: Union[str, NtpClockType] = NtpClockType.client_sent
    ) -> ClockTime:
        return TzUtils.get_ntp_clock(server, kind)

    def ntp_raw(self, server: str = "europe") -> NtpTime:
        return TzUtils.get_ntp_time(server)


class TimezoneMap:
    def __init__(self, cache: TimezoneMapBackend):
        self._cache = cache
        self._map = None

    Types = Types
    Errors = Errors

    def mapping(self) -> TzMapType:
        self._ensure()
        return deepcopy(self._map)

    @property
    def clocks(self) -> Clocks:
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

    @classmethod
    def new_cached(
        cls,
        path: Path = Path.home() / ".timezone-map.json",
        expiration_mins: int = 43830,
    ) -> TimezoneMap:
        return TimezoneMap(TimezoneMapFilesysCache(path, expiration_mins))


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
    print(my_zone.tagged.now_local_ntp(only=False))


__all__ = ["TimezoneMap", "TimezoneMaps"]
