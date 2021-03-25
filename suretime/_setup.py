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

Code that performs initialization for suretime.
"""

from __future__ import annotations
import logging
import os
from importlib.metadata import metadata as load_metadata
from importlib.metadata import PackageNotFoundError
from zoneinfo import ZoneInfo

logger = logging.getLogger("suretime")


if os.name == "nt":
    logger.warning(f"On Windows, timezones are mapped ambiguously to IANA timezones.")
    logger.warning(
        f"On most Windows systems, the monotonic system clock has only millisecond resolution."
    )

try:
    tzdata_vr = load_metadata("tzdata")["version"]
    logger.info(f"Using tzdata version {tzdata_vr}")
except PackageNotFoundError:
    logger.warning(
        f"tzdata not found, so using built-in timezone, which may differ between systems."
    )

# Let's test we don't get a ZoneInfoNotFoundError
UTC = ZoneInfo("UTC")


__all__ = ["logger"]
