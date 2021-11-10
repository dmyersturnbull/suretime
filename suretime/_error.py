"""
Exception classes for suretime.

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


class SuretimeError(Exception):
    """Any suretime-specific error."""


class SuretimeValueError(SuretimeError, ValueError):
    """Any suretime-specific ValueError."""  # for convenience


class CannotMapTzError(SuretimeValueError):
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


class DatetimeHasZoneError(SuretimeValueError):
    """
    Raised when a zone is unexpectedly present in a datetime.
    """


class DatetimeMissingZoneError(SuretimeValueError):
    """
    Raised when a datetime lacks a required zone.
    """


class ZoneMismatchError(SuretimeValueError):
    """
    Raised when two zones needed to match.
    """


class ClockMismatchError(SuretimeValueError):
    """
    Raised when two clocks needed to match.
    """


class DatetimeParseError(SuretimeValueError):
    """
    Raised on failure to parse a datetime format.
    """


class InvalidIntervalError(SuretimeValueError):
    """
    Raised when an interval does not make sense.
    """


__all__ = [
    "CannotMapTzError",
    "DatetimeHasZoneError",
    "DatetimeMissingZoneError",
    "DatetimeParseError",
    "InvalidIntervalError",
    "MappedTzNotFoundError",
    "MappedTzNotUniqueError",
    "SuretimeError",
    "SuretimeValueError",
    "ZoneMismatchError",
]
