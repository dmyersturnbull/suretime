"""
Model classes for suretime.

Copyright 2021 Douglas Myers-Turnbull

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. See the License for the specific language governing
permissions and limitations under the License.

Model and utility classes for suretime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import FrozenSet, Optional, Union
from zoneinfo import ZoneInfo

from suretime import SuretimeGlobals
from suretime._clock import NtpClockType, TzUtils
from suretime._error import MappedTzNotFoundError, MappedTzNotUniqueError
from suretime._generic_zone import GenericTimezone
from suretime._model import DatetimeMissingZoneError, TaggedDatetime, TaggedInterval

empty_frozenset = frozenset([])


@dataclass(frozen=True, repr=True, order=True)
class ExactTimezone:
    """
    A timezone that matches a single IANA ZoneInfo, with info about the source zone.

    Attributes:
        name: The name of the zone (e.g. Mountain Standard Time) or America/Los_Angeles
        territory: None for IANA zones, the 2-letter territory code,
                   or "primary" if the zone is missing
        iana: set of IANA zones that match, sorted alphabetically by name
    """

    name: str
    territory: Optional[str]
    iana: ZoneInfo


class Zones:
    def __init__(self, mp):
        self._map = mp

    def utc(self) -> ZoneInfo:
        return timezone.utc

    def list(self) -> FrozenSet[str]:
        return frozenset(sorted(self._map.keys()))

    def only_local(
        self, territory: Optional[str] = "primary", *, sys: bool = True, etc: bool = True
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
        self, territory: Optional[str] = "primary", *, sys: bool = True, etc: bool = True
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
        self, territory: Optional[str] = "primary", *, sys: bool = True, etc: bool = True
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


@dataclass(frozen=True, repr=True)
class Tagged:
    zones: Zones

    def interval(self, start: TaggedDatetime, end: TaggedDatetime) -> TaggedInterval:
        return TaggedInterval(start, end)

    def now_local_sys(
        self,
        territory: Optional[str] = "primary",
        *,
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
        *,
        only: bool = False,
        etc: bool = True,
        server: str = SuretimeGlobals.NTP_SERVER,
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
        ntp_server: str = SuretimeGlobals.NTP_SERVER,
        ntp_clock: Union[str, NtpClockType] = NtpClockType.client_sent,
    ) -> TaggedDatetime:
        dt = datetime.now(timezone.utc)
        clock_time = TzUtils.get_ntp_clock(ntp_server, ntp_clock)
        return TaggedDatetime(dt, timezone.utc, timezone.utc, clock_time.nanos, clock_time.clock)

    def exact(self, zoned: datetime) -> TaggedDatetime:
        clock_time = TzUtils.get_clock_time()
        info = zoned.tzinfo.tzname(zoned)
        if info is None:
            raise DatetimeMissingZoneError(f"Datetime {zoned} has no zone")
        info = ZoneInfo(info)
        source = GenericTimezone(str(info), None, frozenset({info}))
        return TaggedDatetime(zoned, info, source, clock_time.nanos, clock_time.clock)

    def _get(self, dt: datetime, territory: Optional[str], only: bool) -> TaggedDatetime:
        clock_time = TzUtils.get_clock_time()
        tz = dt.tzinfo.tzname(dt)
        matches = self.zones.all(tz, territory)
        if only:
            iana = self.zones.only(tz, territory)
        else:
            iana = self.zones.first(tz, territory)
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
    ) -> TaggedDatetime:
        if ntp_server is not None:
            if ntp_clock is None:
                raise AssertionError("ntp_attribute must be non-None if ntp_server is non-None")
            clock_time = TzUtils.get_ntp_clock(ntp_server, ntp_clock)
        else:
            clock_time = TzUtils.get_clock_time()
        matches = self.zones.all_local(territory, sys=sys, etc=etc)
        if only:
            iana = self.zones.only_local(territory, sys=sys, etc=etc)
        else:
            iana = self.zones.first_local(territory, sys=sys, etc=etc)
        local_now = datetime.now(timezone.utc).astimezone()
        original = GenericTimezone(local_now.tzname(), territory, matches)
        return TaggedDatetime(local_now, iana, original, clock_time.nanos, clock_time.clock)


__all__ = ["ExactTimezone", "GenericTimezone", "Tagged", "Zones"]
