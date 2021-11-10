"""
Formatting of datetimes.

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

from datetime import datetime


class DtFormatCodes:
    """
    For sane people who never memorized the full list of format codes.
    """

    weekday_locale_short = "%a"
    weekday_locale_full = "%A"
    weekday_decimal = "%w"
    day = "%d"
    month_locale_short = "%b"
    month_locale_full = "%B"
    month = "%m"
    year_2_digit = "%y"
    year = "%Y"
    hour = "%H"
    hour_12_hour = "%I"
    am_pm = "%p"
    minute = "%M"
    second = "%S"
    microsecond = "%f"
    utc_offset = "%z"
    timezone_name = "%Z"
    day_of_year = "%j"
    week_of_year_sunday_first = "%U"
    week_of_year_monday_first = "%W"
    locale_datetime = "%c"
    locale_date = "%x"
    locale_time = "%X"
    literal_percent_sign = "%%"
    year_with_greater_part_of_week = "%G"
    weekday_monday_first = "%u"
    week_of_year_monday_first_with_monday_as_day_1 = "%V"


class DatetimeFormats:
    """
    Common datetime formats.
    """

    iso = "%y-%M-%d %H:%M:%S:%i"
    filesys_long = "%Y-%m-%d_%H_%M_%S"
    filesys_short = "%Y%m%d_%H%M%S"
    pretty = "%y-%M-%d %H:%M:%S"

    @classmethod
    def format_filesys(
        cls, dt: datetime, *, offset: bool = True, micros: bool = True, short: bool = True
    ) -> str:
        fmt = DatetimeFormats.filesys_short if short else DatetimeFormats.filesys_long
        fmt += (".%i" if micros else "") + ("%z" if offset else "")
        return dt.strftime(fmt)

    @classmethod
    def format_pretty(
        cls, dt: datetime, *, offset: bool = True, micros: bool = True, space: str = " "
    ) -> str:
        fmt = DatetimeFormats.pretty
        fmt += (".%i" if micros else "") + ("%z" if offset else "")
        return dt.strftime(fmt).replace(" ", space)

    @classmethod
    def format_iso(cls, dt: datetime, *, space: str = " ") -> str:
        return dt.strftime(DatetimeFormats.iso).replace(" ", space)


__all__ = ["DatetimeFormats", "DtFormatCodes"]
