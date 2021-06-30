"""
Model classes for suretime.

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

Model and utility classes for suretime.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
import logging
from dataclasses import dataclass
from decimal import Decimal
from functools import total_ordering
from typing import Mapping, FrozenSet, Dict, Union, Optional
from zoneinfo import ZoneInfo

import decimal

from suretime._utils import Clock, ClockTime

logger = logging.getLogger("suretime")
TzMapType = Mapping[str, Mapping[str, FrozenSet[ZoneInfo]]]
TzDictType = Dict[str, Dict[str, FrozenSet[ZoneInfo]]]
ROUNDING = decimal.ROUND_HALF_DOWN


class CannotMapTzError(Exception):
    """
    Raised whenever a timezone name could not be mapped to an IANA zone.
    """


class MappedTzNotUniqueError(CannotMapTzError):
    """
    Raised when there is more than 1 IANA zone for a zone.
    """


class MappedTzNotFoundError(CannotMapTzError):
    """
    Raised when there were no IANA zones matching a zone.
    """


class DatetimeHasZoneError(ValueError):
    """
    Raised when a zone is unexpectedly present in a datetime.
    """


class DatetimeMissingZoneError(ValueError):
    """
    Raised when a datetime lacks a required zone.
    """


class DatetimeParseError(ValueError):
    """
    Raised on failure to parse a datetime format.
    """


class InvalidIntervalError(ValueError):
    """
    Raised when an interval does not make sense.
    """


@dataclass(frozen=True, repr=True, order=True)
class GenericTimezone:
    """
    A generic timezone that matches zero or more IANA timezones.
    Contains the source zone (e.g. America/Los_Angeles or Mountain Standard Time),
    along with the territory.

    Attributes:
        name: The name of the zone (e.g. Mountain Standard Time) or America/Los_Angeles
        territory: None for IANA zones, the 2-letter territory code,
                   or "primary" if the zone is missing
        ianas: set of IANA zones that match, sorted alphabetically by name
    """

    name: str
    territory: Optional[str]
    ianas: FrozenSet[ZoneInfo]

    @property
    def is_iana(self) -> bool:
        return len(self.ianas) == 1 and self.name == next(iter(self.ianas))

    @property
    def has_iana(self) -> bool:
        return len(self.ianas) > 0


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


@total_ordering
@dataclass(frozen=True, repr=True)
class ZonedDatetime:
    dt: datetime
    zone: ZoneInfo
    source: Optional[GenericTimezone]

    def __post_init__(self):
        if self.dt.tzname() is None:
            raise DatetimeMissingZoneError(
                f"A {self.__class__.__name__} {self} cannot be created from a local datetime"
            )

    @classmethod
    def parse(cls, s: str) -> ZonedDatetime:
        """
        Parses a datetime with a zone.
        Counterpart to ``iso_with_zone``.
        """
        pat = re.compile(r"^ *([^[]+)\[([\/A-Za-z0-9_\-+]+)] *$")
        match = pat.fullmatch(s)
        if match is None:
            raise DatetimeParseError(f"Could not parse {s} to zoned datetime")
        raw_dt, zone = match.group(1), match.group(2)
        zone = ZoneInfo(zone)
        dt = raw_dt.replace("Z", "+00:00").strip().replace(" ", "T").replace(",", ".")
        dt = datetime.fromisoformat(dt).astimezone(zone)
        return ZonedDatetime(dt, zone, None)

    @property
    def utc(self) -> ZonedDatetime:
        dt = self.dt.astimezone(tz=timezone.utc)
        return ZonedDatetime(dt, ZoneInfo(dt.tzname()), self.source)

    @property
    def iso(self) -> str:
        return self.dt.isoformat()

    @property
    def iso_full(self) -> str:
        return self.dt.isoformat(timespec="microseconds")

    @property
    def iso_with_zone(self) -> str:
        z = str(self.zone)
        if z == "UTC":
            z = "Etc/UTC"
        return f"{self.dt.isoformat(timespec='microseconds').replace('+00:00', 'Z')} [{z}]"

    def is_identical_to(self, other: ZonedDatetime) -> bool:
        us = (self.dt, self.source, self.zone)
        them = (other.dt, other.source, other.zone)
        return us == them

    def __eq__(self, other: Union[datetime, ZonedDatetime]):
        return self.utc == self.__to_utc(other)

    def __lt__(self, other: Union[datetime, ZonedDatetime]):
        return self.utc < self.__to_utc(other)

    def __to_utc(self, other: Union[datetime, ZonedDatetime]) -> datetime:
        if isinstance(other, datetime):
            if other.tzinfo is None:
                raise DatetimeMissingZoneError("Cannot compare zoned and non-zoned datetimes")
            return other.astimezone(tz=timezone.utc)
        elif isinstance(other, ZonedDatetime):
            return other.dt.astimezone(tz=timezone.utc)
        else:
            raise TypeError(f"Cannot compare type {type(other)} to zoned datetime")

    def __str__(self) -> str:
        return f"({self.dt.isoformat()} [{self.zone}])"


@dataclass(frozen=True, repr=True)
class TaggedDatetime(ZonedDatetime):
    clock_ns: int
    clock: Clock

    @property
    def utc(self) -> TaggedDatetime:
        dt = self.dt.astimezone(timezone.utc)
        return TaggedDatetime(dt, timezone.utc, self.source, self.clock_ns, self.clock)

    @property
    def clock_time(self) -> ClockTime:
        return ClockTime(self.clock_ns, self.clock)

    @property
    def clock_sec(self) -> float:
        # float will be exact
        return self.clock_ns / 1e9

    @property
    def use_clock_as_dt(self) -> Optional[TaggedDatetime]:
        """
        Returns a new TaggedDatetime that uses this *clock* as the main datetime.
        Requires that ``self.clock.info.is_epoch`` is true.
        Otherwise, returns None.
        If ``is_epoch`` is true, converts to a datetime using ``datetime.fromtimestamp``.
        Uses ``timezone.utc`` as the zone and None for the source.
        Keeps self.clock and self.clock_ns as-is.

        Returns:
            A new TaggedDatetime, or None
        """
        if self.clock.info.is_epoch:
            dt = datetime.fromtimestamp(self.clock_sec, timezone.utc)
            return TaggedDatetime(dt, timezone.utc, None, self.clock_ns, self.clock)
        return None

    def at_clock(self, clock: ClockTime) -> TaggedDatetime:
        """
        Returns a TaggedDatetime like this one but at the new nanosecond clock time.

        """
        if clock.clock != self.clock:
            raise ValueError(f"Clock {clock.clock.name} is not {self.clock.name}")
        return self.at_nanos(clock.nanos)

    def at_nanos(self, ns: int) -> TaggedDatetime:
        """
        Return a TaggedDatetime like this one but at the new nanosecond clock time.

        .. caution::

            The nanosecond value must be from the same clock.
        """
        delta = ns - self.clock_ns
        dt = self.dt + timedelta(microseconds=delta // 1000)
        return TaggedDatetime(dt, self.zone, self.source, ns, self.clock)

    def __sub__(self, delta: timedelta):
        return self + (-delta)

    def __add__(self, delta: timedelta):
        ns = delta.microseconds * 1000
        return TaggedDatetime(self.dt + delta, self.zone, self.source, ns, self.clock)

    def is_identical_to(self, other: TaggedDatetime) -> bool:
        us = (self.dt, self.zone, self.source, self.clock_ns, self.clock)
        them = (other.dt, other.zone, other.source, other.clock_ns, other.clock)
        return us == them


@dataclass(frozen=True, repr=True, order=True)
class Duration:
    _start: datetime
    _end: datetime

    @property
    def delta(self) -> timedelta:
        return self._end - self._start

    @property
    def iso(self) -> str:
        """
        Returns an ISO 8601-formatted duration string.
        For example: ``D2Y5M22DTH0M36S42.310837``
        Note that a period (.) is always used as the decimal separator.
        """
        start = self._start
        end = self._end
        y = end.year - start.year
        m = end.month - start.month
        d = end.day - start.day
        hr = end.hour - start.hour
        mn = end.minute - start.minute
        micro = Decimal(end.second - start.second) + (
            end.microsecond - start.microsecond
        ) / Decimal(1e6)
        micro = micro.quantize(Decimal(1e-6), rounding=ROUNDING)
        micro = str(micro).replace(",", ".")
        if micro.startswith("."):
            micro = "0" + micro
        return f"P{y}Y{m}M{d}DT{hr}H{mn}M{micro}S"

    def __str__(self) -> str:
        return self.iso


@dataclass(frozen=True, repr=True, order=True)
class TaggedInterval:
    start: TaggedDatetime
    end: TaggedDatetime

    def __post_init__(self):
        # Most importantly, this catches cases where the clock reset
        # This could happen after a system restart
        if self.start.utc > self.end.utc:
            raise InvalidIntervalError(f"Start {self.start} is after {self.end}.")
        start_ns, end_ns = self.start.clock_ns, self.end.clock_ns
        if start_ns > end_ns:
            raise InvalidIntervalError(
                f"Clock times for {self.start} and {self.end} are reversed: {start_ns} > {end_ns}"
            )

    @property
    def real_delta(self) -> timedelta:
        return timedelta(microseconds=self.round_real(int(1e9)))

    @property
    def real_nanos(self) -> int:
        return self.end.clock_ns - self.start.clock_ns

    @property
    def wall_delta(self) -> timedelta:
        return self.end.utc.dt - self.start.utc.dt

    @property
    def wall_nanos(self) -> int:
        return int((self.end.utc.dt - self.start.utc.dt).total_seconds() * 1e9)

    @property
    def real_str(self) -> str:
        ns = self.real_nanos
        td = timedelta(seconds=ns // 1e9)
        return str(td) + "." + str(ns % 1e9)

    def round_real(self, exponent: int) -> int:
        if exponent not in {1, 1e3, 1e6, 1e9}:
            raise ValueError(f"Bad exponent {exponent}")
        scale = Decimal(1e9 / exponent)
        nanos = Decimal(self.end.clock_ns) - Decimal(self.start.clock_ns)
        downsized = nanos / scale
        return int(downsized.to_integral_value(decimal.ROUND_HALF_DOWN))

    @property
    def iso(self) -> str:
        """
        Converts to an ISO 8601 interval string with the full start and end.
        Uses ``--`` as the separator.
        """
        return self.start.iso + "--" + self.end.iso

    @property
    def duration(self) -> Duration:
        return Duration(self.start.dt, self.end.dt)

    def __str__(self) -> str:
        return f"{self.start.iso_with_zone} to {self.end.iso_with_zone} ({self.real_nanos}"


__all__ = [
    "TaggedDatetime",
    "TaggedInterval",
    "ZonedDatetime",
    "TzMapType",
    "TzDictType",
    "GenericTimezone",
    "ExactTimezone",
    "CannotMapTzError",
    "MappedTzNotFoundError",
    "MappedTzNotUniqueError",
    "DatetimeHasZoneError",
    "DatetimeMissingZoneError",
    "DatetimeParseError",
    "InvalidIntervalError",
    "Duration",
]
