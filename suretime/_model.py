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

import dataclasses
import decimal
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import cached_property, total_ordering
from typing import Generator, NamedTuple, Optional, Union
from zoneinfo import ZoneInfo

from suretime._clock import Clock, ClockTime
from suretime._error import (
    ClockMismatchError,
    DatetimeMissingZoneError,
    DatetimeParseError,
    InvalidIntervalError,
    ZoneMismatchError,
)
from suretime._generic_zone import GenericTimezone

ROUNDING = decimal.ROUND_HALF_DOWN
_pat = re.compile(r"^ *([^[]+)\[([/A-Za-z0-9_\-+]+)] *$")


class Ymdhmsun(NamedTuple):
    Y: int
    M: int
    D: int
    h: int
    m: int
    s: int
    u: int
    n: int

    @cached_property
    def duration_iso(self) -> str:
        return f"P{self.Y}Y{self.M}M{self.D}DT{self.h}H{self.m}M{self.u}S"


@total_ordering
@dataclass(frozen=True, repr=True)
class AbstractZonedDatetime:
    dt: datetime
    zone: ZoneInfo
    source: Optional[GenericTimezone]

    def __post_init__(self):
        if self.dt.tzname() is None:
            raise DatetimeMissingZoneError(f"Cannot make {self} from an unaware datetime")
        name1 = self.dt.tzinfo.tzname(self.dt)
        name2 = self.zone.tzname(self.dt)
        if name1 != name2:
            raise ZoneMismatchError(f"{self.dt} has zone {name1} != {name2} from ZoneInfo")

    def copy(self, **kwargs) -> AbstractZonedDatetime:
        return dataclasses.replace(self, **kwargs)

    @cached_property
    def offset(self) -> timedelta:
        return self.zone.utcoffset(self.dt)

    @cached_property
    def offset_str(self) -> str:
        offset = self.zone.utcoffset(self.dt)
        s = abs(offset.total_seconds())
        if s == 0:
            return "Z"
        sgn = "−" if offset.total_seconds() < 0 else "+"
        hours = int(s / 3600)
        minutes = int(s / 60 % 60)
        seconds = int(s % 3600)
        h, m, s = str(hours).zfill(2), str(minutes).zfill(2), str(seconds).zfill(2)
        if seconds > 0:
            return sgn + h + ":" + m + ":" + s
        return sgn + h + ":" + m  # more normal

    @cached_property
    def iso(self) -> str:
        return self.dt.isoformat().replace("+00:00", "Z")

    @cached_property
    def iso_full(self) -> str:
        return self.dt.isoformat(timespec="microseconds").replace("+00:00", "Z")

    @cached_property
    def iso_with_zone(self) -> str:
        z = str(self.zone)
        if z == "UTC":
            z = "Etc/UTC"
        return f"{self.dt.isoformat(timespec='microseconds').replace('+00:00', 'Z')} [{z}]"

    @property
    def utc(self) -> AbstractZonedDatetime:
        dt = self.dt.astimezone(tz=timezone.utc)
        return AbstractZonedDatetime(dt, ZoneInfo(dt.tzname()), self.source)

    def __eq__(self, other):
        raise NotImplementedError()

    def __lt__(self, other):
        raise NotImplementedError()

    def __add__(self, delta):
        raise NotImplementedError()

    def __sub__(self, delta):
        raise NotImplementedError()

    def _to_utc(self, other: Union[datetime, AbstractZonedDatetime]) -> datetime:
        if isinstance(other, datetime):
            if other.tzinfo is None:
                raise DatetimeMissingZoneError("Cannot compare zoned and non-zoned datetimes")
            return other.astimezone(tz=timezone.utc)
        elif isinstance(other, AbstractZonedDatetime):
            return other.dt.astimezone(tz=timezone.utc)
        else:
            raise TypeError(f"Cannot compare type {type(other)} to zoned datetime")


@dataclass(frozen=True, repr=True)
class ZonedDatetime(AbstractZonedDatetime):
    @classmethod
    def now_utc(cls) -> ZonedDatetime:
        return ZonedDatetime.of(datetime.now().astimezone(timezone.utc), timezone.utc, source=None)

    @classmethod
    def now(cls, zone: Union[ZoneInfo, str]) -> ZonedDatetime:
        if isinstance(zone, str):
            zone = ZoneInfo(zone)
        return ZonedDatetime.of(datetime.now().astimezone(zone), zone, source=None)

    @classmethod
    def of(
        cls, dt: datetime, zone: Union[ZoneInfo, str], source: Optional[GenericTimezone] = None
    ) -> ZonedDatetime:
        if isinstance(zone, str):
            zone = ZoneInfo(zone)
        return cls(dt, zone, source)

    @classmethod
    def parse(cls, s: str) -> ZonedDatetime:
        """
        Parses a datetime with a zone.
        Counterpart to  :meth:`iso_with_zone`.
        """
        match = _pat.fullmatch(s)
        if match is None:
            raise DatetimeParseError(f"Could not parse {s} to zoned datetime")
        raw_dt, zone = match.group(1), match.group(2)
        zone = ZoneInfo(zone)
        dt = raw_dt.replace("Z", "+00:00").strip().replace(" ", "T").replace(",", ".")
        dt = datetime.fromisoformat(dt).astimezone(zone)
        return cls(dt, zone, None)

    def copy(self, **kwargs) -> ZonedDatetime:
        return dataclasses.replace(self, **kwargs)

    def is_identical_to(self, other: ZonedDatetime) -> bool:
        us = (self.dt, self.source, self.zone)
        them = (other.dt, other.source, other.zone)
        return us == them

    def __eq__(self, other: Union[datetime, ZonedDatetime]):
        return self.utc.dt == self._to_utc(other)

    def __lt__(self, other: Union[datetime, ZonedDatetime]):
        return self.utc.dt < self._to_utc(other)

    def __add__(self, delta: timedelta) -> ZonedDatetime:
        return ZonedDatetime(self.dt + delta, self.zone, self.source)

    def __sub__(self, delta: timedelta) -> ZonedDatetime:
        return ZonedDatetime(self.dt - delta, self.zone, self.source)

    def __str__(self) -> str:
        return f"({self.dt.isoformat()} [{self.zone}])"


@total_ordering
@dataclass(frozen=True, repr=True)
class TaggedDatetime(AbstractZonedDatetime):
    clock_ns: int
    clock: Clock

    @classmethod
    def of(
        cls,
        dt: datetime,
        zone: Union[ZoneInfo, str],
        clock_ns: int,
        clock: Clock,
        source: Optional[GenericTimezone] = None,
    ) -> TaggedDatetime:
        if isinstance(zone, str):
            zone = ZoneInfo(zone)
        return cls(dt, zone, source, clock_ns, clock)

    def copy(self, **kwargs) -> TaggedDatetime:
        return dataclasses.replace(self, **kwargs)

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

    def to(self, end: TaggedDatetime) -> TaggedInterval:
        return TaggedInterval(self, end)

    def at_clock(self, clock: ClockTime) -> TaggedDatetime:
        """
        Returns a TaggedDatetime like this one but at the new nanosecond clock time.

        """
        if clock.clock != self.clock:
            raise ClockMismatchError(f"Clock {clock.clock.name} is not {self.clock.name}")
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

    def is_identical_to(self, other: TaggedDatetime) -> bool:
        us = (self.dt, self.zone, self.source, self.clock_ns, self.clock)
        them = (other.dt, other.zone, other.source, other.clock_ns, other.clock)
        return us == them

    def __sub__(self, delta: timedelta):
        return self + (-delta)

    def __add__(self, delta: timedelta) -> TaggedDatetime:
        ns = delta.microseconds * 1000
        return TaggedDatetime(self.dt + delta, self.zone, self.source, ns, self.clock)

    def __lt__(self, other: TaggedDatetime) -> bool:
        return (self.utc.dt, self.clock_ns) < (self._to_utc(other), other.clock_ns)

    def __eq__(self, other: TaggedDatetime):
        return self.utc.dt == self._to_utc(other) and self.clock_ns == other.clock_ns


@dataclass(frozen=True)
class _Duration:
    _start: datetime
    _end: datetime

    def __post_init__(self):
        if self.microseconds < 0:
            raise ValueError(f"Duration {self} is negative")

    @property
    def microseconds(self) -> int:
        return int(self.delta.total_seconds() * 1000000)

    @cached_property
    def delta(self) -> timedelta:
        return self._end - self._start

    @property
    def approx_long(self) -> str:
        t = self.ymdhmun
        if t.Y > 0:
            return f"{t.Y} years"
        if t.M > 0:
            return f"{t.M} months"
        if t.D > 0:
            return f"{t.D} days"
        if t.h > 0:
            return f"{t.h} hours"
        if t.m > 0:
            return f"{t.m} minutes"
        if t.s > 0:
            return f"{t.s} seconds"
        if t.u > 0:
            return f"{t.M} microseconds"

    @property
    def approx_short(self) -> str:
        t = self.ymdhmun
        if t.Y > 0:
            return f"{t.Y} years"
        if t.M > 0:
            return f"{t.M} month"
        if t.D > 0:
            return f"{t.D} days"
        if t.h > 0:
            return f"{t.h} hr"
        if t.m > 0:
            return f"{t.m} min"
        if t.s > 0:
            return f"{t.s} s"
        if t.u > 0:
            return f"{t.M} µs"

    @cached_property
    def ymdhmun(self) -> Ymdhmsun:
        start, end = self._start, self._end
        return Ymdhmsun(
            Y=end.year - start.year,
            M=end.month - start.month,
            D=end.day - start.day,
            h=end.hour - start.hour,
            m=end.minute - start.minute,
            s=int(end.second - start.second),  # floor
            u=int((end.microsecond - start.microsecond) % 1000),
            n=0,
        )

    @property
    def iso(self) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.iso

    def __repr__(self) -> str:
        return self.iso


@total_ordering
@dataclass(frozen=True)
class Duration(_Duration):
    """"""

    def repeat(self, n_events: Optional[int] = None) -> RepeatingDuration:
        return RepeatingDuration(self._start, self._end, n_events)

    def copy(self, **kwargs) -> Duration:
        return dataclasses.replace(self, **kwargs)

    @cached_property
    def iso(self) -> str:
        """
        Returns an ISO 8601-formatted duration string.
        For example: ``D2Y5M22DTH0M36S42.310837``
        Note that a period (.) is always used as the decimal separator.
        """
        return self.ymdhmun.duration_iso

    def __eq__(self, other: _Duration):
        return self.delta == other.delta

    def __lt__(self, other: _Duration):
        return self.delta < other.delta

    def __sub__(self, delta: timedelta) -> Duration:
        return self + (-delta)

    def __add__(self, delta: timedelta) -> Duration:
        return self.copy(_end=self._start + delta)

    def __mul__(self, scale: float) -> Duration:
        delta = self.delta * scale
        return Duration(self._start, self._start + delta)

    def __truediv__(self, scale: float) -> Duration:
        delta = self.delta / scale
        return Duration(self._start, self._start + delta)


@total_ordering
@dataclass(frozen=True)
class RepeatingDuration(_Duration):
    _n_events: Optional[int]

    def copy(self, **kwargs) -> RepeatingDuration:
        return dataclasses.replace(self, **kwargs)

    @property
    def is_bounded(self) -> bool:
        return self.n_events is not None

    @property
    def n_events(self) -> Optional[int]:
        if self._n_events == -1:
            return None
        return self._n_events

    def at(self, start: ZonedDatetime) -> RepeatingDuration:
        return RepeatingInterval(self._start, self._end, self.n_events, start)

    @property
    def duration(self) -> Duration:
        return Duration(self._start, self._end)

    @cached_property
    def iso(self) -> str:
        n = "" if self.n_events is None else str(self.n_events - 1)
        return "R" + n + self.iso

    def __sub__(self, delta: timedelta) -> RepeatingDuration:
        return self + (-delta)

    def __add__(self, delta: timedelta) -> RepeatingDuration:
        return self.copy(_end=self._start + delta)

    def __mul__(self, scale: float) -> RepeatingDuration:
        delta = self.delta * scale
        return RepeatingDuration(self._start, self._start + delta, self.n_events)

    def __truediv__(self, scale: float) -> RepeatingDuration:
        delta = self.delta / scale
        return RepeatingDuration(self._start, self._start + delta, self.n_events)

    def __eq__(self, other: RepeatingDuration):
        return (self.delta, self.n_events) == (other.delta, self.n_events)

    def __lt__(self, other: RepeatingDuration):
        return (self.delta, self.n_events) < (other.delta, other.n_events)


@dataclass(frozen=True, repr=True)
class RepeatingInterval(RepeatingDuration):
    start: AbstractZonedDatetime

    def copy(self, **kwargs) -> RepeatingInterval:
        return dataclasses.replace(self, **kwargs)

    @cached_property
    def iso(self) -> str:
        n = "" if self.n_events is None else str(self.n_events - 1)
        return "R" + n + self.start.iso + "/" + self.iso

    def slice(self, first: int = 0, last: int = -1, step: int = 1) -> RepeatingInterval:
        if first < 0:
            first = self.n_events - first + 1
        if last < 0:
            last = self.n_events - last + 1
        n = last - first
        w = step * self.delta * n / self.n_events
        return RepeatingInterval(
            _start=self._start + first * w,
            _end=self._end + first * w,
            _n_events=n // step,
            start=self.start + first * w,
        )

    def event(self, event: int) -> AbstractZonedDatetime:
        return self.start + event * self.delta

    def list(self) -> Generator[AbstractZonedDatetime, None, None]:
        for i in range(self.n_events):
            yield self.start + i * self.delta

    def offset(self, offset: timedelta) -> RepeatingInterval:
        return RepeatingInterval(
            self._start + offset,
            self._end + offset,
            self.n_events,
            self.start + offset,
        )

    def __rshift__(self, offset: timedelta) -> RepeatingInterval:
        return self.offset(offset)

    def __lshift__(self, offset: timedelta) -> RepeatingInterval:
        return self.offset(-offset)

    def __sub__(self, delta: timedelta) -> RepeatingInterval:
        return self + (-delta)

    def __add__(self, delta: timedelta) -> RepeatingInterval:
        return self.copy(_end=self._start + delta)

    def __mul__(self, scale: float) -> RepeatingInterval:
        return self.copy(_end=self._start + self.delta * scale)

    def __truediv__(self, scale: float) -> RepeatingInterval:
        return self.copy(_end=self._start + self.delta / scale)

    def __getitem__(
        self, event: Union[int, slice]
    ) -> Union[AbstractZonedDatetime, RepeatingInterval]:
        if isinstance(event, slice):
            return self.slice(event.start, event.stop, event.step)
        return self.event(event)

    def __eq__(self, other: RepeatingInterval):
        return (self.delta, self.n_events, self.start) == (other.delta, self.n_events, self.start)

    def __lt__(self, other: RepeatingInterval):
        return (self.start, self.delta, self.n_events) < (self.start, other.delta, other.n_events)


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

    def copy(self, **kwargs) -> TaggedInterval:
        return dataclasses.replace(self, **kwargs)

    @cached_property
    def real_delta(self) -> timedelta:
        return timedelta(microseconds=self.round_real(int(1e9)))

    @property
    def real_nanos(self) -> int:
        return self.end.clock_ns - self.start.clock_ns

    @cached_property
    def wall_delta(self) -> timedelta:
        return self.end.utc.dt - self.start.utc.dt

    @property
    def wall_seconds(self) -> float:
        return (self.end.utc.dt - self.start.utc.dt).total_seconds()

    @property
    def wall_nanos(self) -> int:
        return int((self.end.utc.dt - self.start.utc.dt).total_seconds() * 1e9)

    @cached_property
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
        return int(downsized.to_integral_value(ROUNDING))

    @property
    def iso(self) -> str:
        """
        Converts to an ISO 8601 interval string with the full start and end.
        """
        return self.start.iso + "/" + self.end.iso

    @property
    def duration(self) -> Duration:
        return Duration(self.start.dt, self.end.dt)

    def repeat(self, n_events: Optional[int] = None) -> RepeatingInterval:
        return RepeatingInterval(self.start.dt, self.end.dt, n_events, self.start)

    def __str__(self) -> str:
        return f"{self.start.iso_with_zone} to {self.end.iso_with_zone} ({self.real_nanos} ns)"


__all__ = [
    "DatetimeMissingZoneError",
    "DatetimeParseError",
    "Duration",
    "GenericTimezone",
    "InvalidIntervalError",
    "RepeatingDuration",
    "RepeatingInterval",
    "TaggedDatetime",
    "TaggedInterval",
    "Ymdhmsun",
    "ZonedDatetime",
]
