# SPDX-FileCopyrightText: Copyright 2021-2023, Contributors to Suretime
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/suretime
# SPDX-License-Identifier: Apache-2.0

"""
Suretime entry point for import.

Use as:

```python
import suretime

suretime.zone.first_local()  # ZoneInfo["America/Los_Angeles"]
```
"""

from datetime import UTC, datetime, timedelta, timezone
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __load
from pathlib import Path
from zoneinfo import ZoneInfo

import suretime._error as errors
from suretime._clock import (
    Clock,
    ClockInfo,
    ClockTime,
    NtpClockType,
    NtpContinents,
    NtpTime,
    SysTzInfo,
)
from suretime._global import SuretimeGlobals
from suretime._mapping import TimezoneMaps
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
from suretime._setup import UTC, logger
from suretime._zone import ExactTimezone, GenericTimezone

pkg = Path(__file__).parent.name
metadata = None
try:
    metadata = __load(pkg)
except PackageNotFoundError:  # pragma: no cover
    logger.error(f"Could not load package metadata for {pkg}. Is it installed?")
    __uri__ = None
    __title__ = None
    __summary__ = None
    __version__ = None
else:
    __uri__ = metadata["home-page"]
    __title__ = metadata["name"]
    __summary__ = metadata["summary"]
    __version__ = metadata["version"]

cache = TimezoneMaps.cached()
clock = cache.clocks
zone = cache.zones
tag = cache.tagged
utc = UTC


def get_ntp_continent() -> str:
    return SuretimeGlobals.NTP_SERVER


def set_ntp_continent(code: str) -> None:
    SuretimeGlobals.NTP_SERVER = code


class SuretimeMeta:
    version = __version__


__all__ = [
    "datetime",
    "timedelta",
    "timezone",
    "ZoneInfo",
    "cache",
    "clock",
    "errors",
    "tag",
    "zone",
    "Duration",
    "RepeatingDuration",
    "RepeatingInterval",
    "TaggedDatetime",
    "TaggedInterval",
    "ZonedDatetime",
    "SuretimeGlobals",
    "SuretimeMeta",
]
