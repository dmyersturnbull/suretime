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

Model and utility classes for ensuretimezone.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
import logging
from dataclasses import dataclass
from functools import total_ordering
from typing import Mapping, FrozenSet, Dict, Union
from zoneinfo import ZoneInfo


logger = logging.getLogger("ensuretimezone")


TzMapType = Mapping[str, Mapping[str, FrozenSet[ZoneInfo]]]
TzDictType = Dict[str, Dict[str, FrozenSet[ZoneInfo]]]


@total_ordering
@dataclass(frozen=True, repr=True)
class ZonedDatetime:
    local: datetime
    zone: ZoneInfo
    original_zone: str

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

    def is_identical_to(self, other: ZonedDatetime) -> bool:
        return (self.local, self.original_zone, self.zone) == (
            other.local,
            other.original_zone,
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


__all__ = ["TaggedDatetime", "TaggedInterval", "TzMapType", "TzDictType"]
