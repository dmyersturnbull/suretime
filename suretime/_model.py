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

Model and utility classes for suretime.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
import logging
from dataclasses import dataclass
from functools import total_ordering
from typing import Mapping, FrozenSet, Dict, Union, Optional
from zoneinfo import ZoneInfo


logger = logging.getLogger("suretime")


TzMapType = Mapping[str, Mapping[str, FrozenSet[ZoneInfo]]]
TzDictType = Dict[str, Dict[str, FrozenSet[ZoneInfo]]]


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
    local: datetime
    zone: ZoneInfo
    source: GenericTimezone

    def __post_init__(self):
        if self.local.tzname() is None:
            raise ValueError(
                f"A {self.__class__.__name__} {self} cannot be created from a local datetime"
            )

    @property
    def as_utc(self) -> datetime:
        return self.local.astimezone(timezone.utc)

    @property
    def iso(self) -> str:
        return f"{self.local.isoformat()}"

    @property
    def iso_utc(self) -> str:
        return f"{self.local.astimezone(timezone.utc).isoformat()}"

    @property
    def iso_with_zone(self) -> str:
        return f"{self.local.isoformat(timespec='microseconds')} [{self.zone}]"

    @property
    def original_zone(self) -> str:
        return self.source.name

    def is_identical_to(self, other: ZonedDatetime) -> bool:
        return (self.local, self.source, self.zone) == (
            other.local,
            other.source,
            other.zone,
        )

    def __eq__(self, other: Union[datetime, ZonedDatetime]):
        return self.as_utc == self.__to_utc(other)

    def __lt__(self, other: Union[datetime, ZonedDatetime]):
        return self.as_utc < self.__to_utc(other)

    def __to_utc(self, other: Union[datetime, ZonedDatetime]) -> datetime:
        if isinstance(other, datetime):
            if other.tzinfo is None:
                raise ValueError(f"Cannot compare zoned datetime to a datetime without a zone")
            return other.astimezone(tz=timezone.utc)
        elif isinstance(other, ZonedDatetime):
            return other.local.astimezone(tz=timezone.utc)
        else:
            raise TypeError(f"Cannot compare type {type(other)} to zoned datetime")

    def __str__(self) -> str:
        return f"({self.local.isoformat()} [{self.zone}])"


@dataclass(frozen=True, repr=True)
class TaggedDatetime(ZonedDatetime):
    mono_clock_ns: int

    def is_identical_to(self, other: ZonedDatetime) -> bool:
        return (self.local, self.original_zone, self.zone, self.mono_clock_ns) == (
            other.local,
            other.original_zone,
            other.zone,
            self.mono_clock_ns,
        )


@dataclass(frozen=True, repr=True, order=True)
class TaggedInterval:
    start: TaggedDatetime
    end: TaggedDatetime

    def __post_init__(self):
        # Most importantly, this catches cases where the clock reset
        # This could happen after a system restart
        if self.start.as_utc > self.end.as_utc:
            raise ValueError(f"Start {self.start} is after {self.end}.")
        start_ns, end_ns = self.start.mono_clock_ns, self.end.mono_clock_ns
        if start_ns > end_ns:
            raise ValueError(
                f"Clock times for {self.start} and {self.end} are reversed: {start_ns} > {end_ns}"
            )

    @property
    def n_nanos_real(self) -> int:
        return self.end.mono_clock_ns - self.start.mono_clock_ns

    @property
    def n_micros_real(self) -> int:
        return int(round((self.end.mono_clock_ns - self.start.mono_clock_ns) / 1000))

    @property
    def delta_real_time(self) -> timedelta:
        return timedelta(microseconds=self.n_micros_real)

    @property
    def delta_calendar_time(self) -> timedelta:
        return self.end.as_utc - self.start.as_utc

    @property
    def real_delta_str(self) -> str:
        micros = self.n_micros_real
        return str(timedelta(microseconds=micros)) + "." + str(self.n_nanos_real % 1000)

    def __str__(self) -> str:
        return f"{self.start.iso_with_zone} to {self.end.iso_with_zone} ({self.n_nanos_real}"


__all__ = [
    "TaggedDatetime",
    "TaggedInterval",
    "TzMapType",
    "TzDictType",
    "GenericTimezone",
    "ExactTimezone",
    "CannotMapTzError",
    "MappedTzNotFoundError",
    "MappedTzNotUniqueError",
    "DatetimeHasZoneError",
    "DatetimeMissingZoneError",
]
