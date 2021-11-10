"""
Utility collections of types.

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

Code that maps Windows timezones.
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

from suretime._clock import (
    Clock,
    ClockInfo,
    ClockTime,
    NtpClockType,
    NtpContinents,
    NtpTime,
    SysTzInfo,
)
from suretime._error import (
    CannotMapTzError,
    ClockMismatchError,
    DatetimeHasZoneError,
    DatetimeParseError,
    MappedTzNotFoundError,
    MappedTzNotUniqueError,
    ZoneMismatchError,
)
from suretime._mapping import Clocks
from suretime._model import (
    Duration,
    InvalidIntervalError,
    RepeatingDuration,
    RepeatingInterval,
    TaggedDatetime,
    TaggedInterval,
    Ymdhmsun,
    ZonedDatetime,
)
from suretime._zone import ExactTimezone, GenericTimezone


class Errors:
    DatetimeParseError = DatetimeParseError
    CannotMapTzError = CannotMapTzError
    DatetimeHasZoneError = DatetimeHasZoneError
    MappedTzNotFoundError = MappedTzNotFoundError
    MappedTzNotUniqueError = MappedTzNotUniqueError
    InvalidIntervalError = InvalidIntervalError
    ClockMismatchError = ClockMismatchError
    ZoneMismatchError = ZoneMismatchError


class Types:
    GenericTimezone = GenericTimezone
    TaggedDatetime = TaggedDatetime
    TaggedInterval = TaggedInterval
    ExactTimezone = ExactTimezone
    Clocks = Clocks
    ZoneInfo = ZoneInfo
    ZonedDatetime = ZonedDatetime
    Duration = Duration
    RepeatingDuration = RepeatingDuration
    RepeatingInterval = RepeatingInterval
    Clock = Clock
    ClockTime = ClockTime
    ClockInfo = ClockInfo
    SysTzInfo = SysTzInfo
    NtpTime = NtpTime
    NtpClockType = NtpClockType
    NtpContinents = NtpContinents
    Ymdhmsun = Ymdhmsun


__all__ = ["Errors", "Types"]
