"""
Suretime entry point for import.

Use as:

.. code-block::

  import suretime
  suretime.zone.first_local()  # ZoneInfo["America/Los_Angeles"]

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
"""

from datetime import datetime, timedelta, timezone
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __load
from zoneinfo import ZoneInfo

from suretime._global import SuretimeGlobals
from suretime._mapping import TimezoneMaps
from suretime._setup import UTC, logger
from suretime._type import Errors as errors
from suretime._type import Types as types

cache = TimezoneMaps.cached()
clock = cache.clocks
zone = cache.zones
tag = cache.tagged
utc = UTC

ZoneInfo = ZoneInfo
GenericTimezone = types.GenericTimezone
TaggedDatetime = types.TaggedDatetime
TaggedInterval = types.TaggedInterval
ExactTimezone = types.ExactTimezone
ZonedDatetime = types.ZonedDatetime
RepeatingDuration = types.RepeatingDuration
RepeatingInterval = types.RepeatingInterval
Duration = types.Duration


def get_ntp_continent() -> str:
    return SuretimeGlobals.NTP_SERVER


def set_ntp_continent(code: str) -> None:
    SuretimeGlobals.NTP_SERVER = code


metadata = None
try:
    metadata = __load("suretime")
    __status__ = "Development"
    __copyright__ = "Copyright 2021"
    __date__ = "2021-01-20"
    __uri__ = metadata["home-page"]
    __title__ = metadata["name"]
    __summary__ = metadata["summary"]
    __license__ = metadata["license"]
    __version__ = metadata["version"]
    __author__ = metadata["author"]
    __maintainer__ = metadata["maintainer"]
    __contact__ = metadata["maintainer"]
except PackageNotFoundError:  # pragma: no cover
    logger.error("Could not load package metadata for suretime. Is it installed?")


if __name__ == "__main__":  # pragma: no cover
    if metadata is not None:
        print(f"suretime (v{metadata['version']})")
    else:
        print(f"Unknown project info for suretime")
    my_zone = TimezoneMaps.non_cached()
    print(my_zone.tagged.now_local_ntp(only=False))


__all__ = [
    "datetime",
    "timedelta",
    "timezone",
    "ZoneInfo",
    "cache",
    "clock",
    "errors",
    "tag",
    "types",
    "zone",
    "Duration",
    "RepeatingDuration",
    "RepeatingInterval",
    "TaggedDatetime",
    "TaggedInterval",
    "ZonedDatetime",
]
