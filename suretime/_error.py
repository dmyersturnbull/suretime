# SPDX-FileCopyrightText: Copyright 2021-2023, Contributors to Suretime
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/suretime
# SPDX-License-Identifier: Apache-2.0

"""
Exception classes for suretime.

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
    "ClockMismatchError",
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
