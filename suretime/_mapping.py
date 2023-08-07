# SPDX-FileCopyrightText: Copyright 2021-2023, Contributors to Suretime
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/suretime
# SPDX-License-Identifier: Apache-2.0

"""
Main code for suretime.

Code that maps Windows timezones.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import platformdirs

from suretime import SuretimeGlobals
from suretime._cache import TimezoneMapBackend, TimezoneMapFilesysCache
from suretime._clock import ClockTime, NtpClockType, NtpTime, TzUtils
from suretime._zone import Tagged, Zones

DEFAULT_CACHE_DIR = platformdirs.user_cache_path("suretime")


class Clocks:
    def sys(self) -> ClockTime:
        return TzUtils.get_clock_time()

    def ntp(
        self,
        *,
        server: str = SuretimeGlobals.NTP_SERVER,
        kind: str | NtpClockType = NtpClockType.client_sent,
    ) -> ClockTime:
        return TzUtils.get_ntp_clock(server, kind)

    def ntp_raw(self, *, server: str = SuretimeGlobals.NTP_SERVER) -> NtpTime:
        return TzUtils.get_ntp_time(server)

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __str__(self) -> str:
        return self.__class__.__name__

    def __eq__(self, other: Clocks):
        if not isinstance(other, Clocks):
            msg = f"Cannot compare {type(other)}"
            raise TypeError(msg)
        return True


class TimezoneMap:
    def __init__(self, cache: TimezoneMapBackend) -> None:
        self._cache = cache
        self._map = None

    @property
    def clocks(self) -> Clocks:
        return Clocks()

    @property
    def zones(self) -> Zones:
        self._ensure()
        return Zones(self._map)

    @property
    def tagged(self) -> Tagged:
        self._ensure()
        return Tagged(self.zones)

    def _ensure(self) -> None:
        if self._map is None:
            self._map = self._cache.get()

    @classmethod
    def new_cached(
        cls,
        path: Path = DEFAULT_CACHE_DIR,
        expiration_mins: int = 43830,
    ) -> TimezoneMap:
        return TimezoneMap(TimezoneMapFilesysCache(path, expiration_mins))


class TimezoneMaps:
    @classmethod
    def cached(
        cls,
        path: Path = Path.home() / ".timezone-map.json",
        *,
        expiration_mins: int = 43830,
    ) -> TimezoneMap:
        return TimezoneMap(TimezoneMapFilesysCache(path, expiration_mins))

    @classmethod
    def non_cached(cls) -> TimezoneMap:
        return TimezoneMap(TimezoneMapFilesysCache(None))


__all__ = ["TimezoneMap", "TimezoneMaps"]
