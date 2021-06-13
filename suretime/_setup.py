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
from zoneinfo import ZoneInfo

from suretime._utils import TzUtils

logger = logging.getLogger("suretime")
_import_clock_time = TzUtils.get_clock_time()

if os.name == "nt":
    logger.warning(f"On Windows, timezones are mapped ambiguously to IANA timezones.")
    logger.warning(f"On Windows, the monotonic clock only has millisecond resolution.")

if os.name == "posix" and _import_clock_time.clock.name == "monotonic":
    logger.warning(
        f"Found monotonic clock in Linux incorrectly stops on suspend. Better clocks not found."
    )

try:
    import tzdata

    tzdata_vr = tzdata.__version__
    logger.info(f"Using tzdata version {tzdata_vr}")
except ImportError:
    tzdata = None
    logger.warning(f"tzdata not found; using built-in, which may differ between systems.")

# Let's test we don't get a ZoneInfoNotFoundError
UTC = ZoneInfo("Etc/UTC")


__all__ = ["logger"]
