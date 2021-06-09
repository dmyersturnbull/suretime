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

Project metadata for suretime.
"""

from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __load
from pathlib import Path

from suretime._setup import logger
from suretime._mapping import TimezoneMap, TimezoneMaps
from suretime._cache import TimezoneMapBackend, TimezoneMapFilesysCache
from suretime._model import TaggedDatetime, TaggedInterval


pkg = Path(__file__).absolute().parent.name
metadata = None
try:
    metadata = __load(pkg)
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
    logger.error(f"Could not load package metadata for {pkg}. Is it installed?")


TzMap = TimezoneMaps.cached()


if __name__ == "__main__":  # pragma: no cover
    if metadata is not None:
        print(f"{pkg} (v{metadata['version']})")
    else:
        print(f"Unknown project info for {pkg}")


__all__ = [
    "TzMap",
    "datetime",
    "timedelta",
    "timezone",
    "ZoneInfo",
    "TimezoneMap",
    "TimezoneMaps",
    "TimezoneMapBackend",
    "TimezoneMapFilesysCache",
    "TaggedDatetime",
    "TaggedInterval",
]
