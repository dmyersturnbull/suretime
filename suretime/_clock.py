"""
System utils for suretime.

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

Code that performs initialization for suretime.
"""

from __future__ import annotations

import dataclasses
import decimal
import enum
import logging
import os
import platform
import time
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import FrozenSet, Optional, Union

from ntplib import NTPClient

from suretime._error import ZoneMismatchError
from suretime._global import SuretimeGlobals

logger = logging.getLogger("suretime")


class NtpContinents:
    known: FrozenSet[str] = frozenset(
        {
            "antarctica",
            "asia",
            "europe",
            "north-america",
            "oceana",
            "south-america",
        }
    )

    @classmethod
    def of(cls, name: str) -> str:
        name = name.lower().replace(" ", "-").replace("_", "-")
        if name not in NtpContinents.known:
            raise LookupError(
                f"Unknown NTP continent {name} (allowed: {','.join(NtpContinents.known)})"
            )
        return name


@dataclass(frozen=True, order=True, repr=True)
class SysTzInfo:
    zone_name: str
    offset_mins: Optional[int]


@dataclass(frozen=True, order=True, repr=True)
class ClockInfo:
    adjustable: bool
    implementation: Optional[str]
    monotonic: bool
    resolution: Optional[float]
    is_ntp: bool
    server: Optional[str]
    is_epoch: bool

    def copy(self, **kwargs) -> ClockInfo:
        return dataclasses.replace(self, **kwargs)


@dataclass(frozen=True, order=True, repr=True)
class NtpTime:
    server: str
    stratum: int
    root_dispersion: float
    root_delay: float
    precision: int
    client_sent: float
    server_received: float
    server_sent: float
    client_received: float

    @property
    def round_trip(self) -> timedelta:
        return timedelta(seconds=self.client_received - self.client_sent)

    def copy(self, **kwargs) -> NtpTime:
        return dataclasses.replace(self, **kwargs)


class NtpClockType(enum.Enum):
    client_sent = enum.auto()
    server_received = enum.auto()
    server_sent = enum.auto()
    client_received = enum.auto()

    @property
    def name(self) -> str:
        return self._name_.replace("_", "-")

    @classmethod
    def of(cls, clock: Union[str, NtpClockType]) -> NtpClockType:
        if isinstance(clock, NtpClockType):
            return clock
        return cls[clock.lower().strip().replace("-", "_").replace(" ", "_")]


@dataclass(frozen=True, order=True, repr=True)
class Clock:
    name: str
    const: Optional[int]
    info: Optional[ClockInfo]

    @classmethod
    def empty(cls) -> Clock:
        return Clock("clock", None, None)

    @classmethod
    def system(cls, name: str, const: int) -> Clock:
        if name == "boottime":
            info = ClockInfo(False, None, True, None, False, None, False)
        else:
            try:
                info = time.get_clock_info(name)
                info = ClockInfo(
                    info.adjustable,
                    info.implementation,
                    info.monotonic,
                    info.resolution,
                    False,
                    None,
                    False,
                )
            except ValueError:
                info = None
        return Clock(name, const, info)

    def copy(self, **kwargs) -> Clock:
        return dataclasses.replace(self, **kwargs)


@dataclass(frozen=True, order=True, repr=True)
class ClockTime:
    nanos: int
    clock: Clock

    def copy(self, **kwargs) -> ClockTime:
        return dataclasses.replace(self, **kwargs)


class TzUtils:
    @classmethod
    def get_ntp_clock(
        cls,
        server: str = SuretimeGlobals.NTP_SERVER,
        attribute: Union[str, NtpClockType] = NtpClockType.client_sent,
    ) -> ClockTime:
        attribute = NtpClockType.of(attribute).name
        data = cls.get_ntp_time(server=server)
        x = getattr(data, attribute.replace("-", "_"))
        epoch = cls.round_s_to_ns(x)
        clock = Clock(
            f"{server}:{attribute}",
            None,
            ClockInfo(True, f"ntp:{data.stratum}", False, data.precision, True, server, True),
        )
        return ClockTime(epoch, clock)

    @classmethod
    def get_ntp_time(cls, server: str = SuretimeGlobals.NTP_SERVER) -> NtpTime:
        server = NtpContinents.of(server)
        server = f"{server}.pool.ntp.org"
        client = NTPClient()
        response = client.request(server, version=4)
        return NtpTime(
            server,
            response.stratum,
            response.precision,
            response.root_dispersion,
            response.root_delay,
            response.orig_timestamp,
            response.recv_timestamp,
            response.tx_timestamp,
            response.dest_timestamp,
        )

    @classmethod
    def round_s_to_ns(cls, sec: float) -> int:
        downsized = Decimal(sec) * Decimal(1e9)
        return int(downsized.to_integral_value(decimal.ROUND_HALF_DOWN))

    @classmethod
    def get_clock_time(cls) -> ClockTime:
        clock = cls.get_clock()
        if clock == Clock("monotonic_ns", None, None):
            return ClockTime(time.monotonic_ns(), clock)
        return ClockTime(time.clock_gettime_ns(clock.const), clock)

    @classmethod
    def get_clock(cls) -> Clock:
        priorities = ["boottime", "monotonic_raw"]  # best first
        for name in priorities:
            attr = f"CLOCK_{name.upper()}"
            if hasattr(time, attr):
                clock = Clock.system(name, getattr(time, attr, name))
                if (
                    clock.info is not None
                    and clock.info.monotonic
                    and hasattr(time, "clock_gettime_ns")
                ):
                    return clock
        return Clock("monotonic_ns", None, None)  # guaranteed for Python 3.5+

    @classmethod
    def get_offset_zone(cls) -> SysTzInfo:
        local = time.localtime()
        # TODO: Are these supposed to be purely by geography, or INCLUDE standard/DST?
        offset = local.tm_gmtoff
        return SysTzInfo(f"Etc/{cls.offset_to_str(offset)}", offset)

    @classmethod
    def offset_to_str(cls, mins: int) -> str:
        if mins == 0:
            return "0"  # make sure we don't have a decimal point
        elif str(mins).startswith("-"):
            return str(mins)
        else:
            return "+" + str(mins)

    @classmethod
    def get_sys_zone(cls) -> Optional[SysTzInfo]:
        if platform.system() == "Windows" and platform.release() in {"NT", "10", "8", "7"}:
            return cls._get_windows_zone()
        else:
            return cls._get_nix_zone()

    @classmethod
    def _get_nix_zone(cls) -> Optional[SysTzInfo]:
        path = Path("/") / "etc" / "timezone"
        from_path = None
        if path.exists():
            try:
                from_path = path.read_text().strip()  # use default encoding
            except OSError:
                pass
        from_env = os.environ.get("TZ")
        if from_env is not None and from_path is not None and from_env != from_path:
            raise ZoneMismatchError(
                f"Contradictory system timezones {from_path} from {path} and {from_env} from $TZ"
            )
        if from_path is not None:
            return SysTzInfo(from_path, None)
        if from_env is not None:
            return SysTzInfo(from_env, None)
        return None

    @classmethod
    def _get_windows_zone(cls) -> Optional[SysTzInfo]:
        import winreg

        key_name = r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation"
        try:
            with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as handle:
                with winreg.OpenKeyEx(handle, key_name) as key:
                    zone, _ = winreg.QueryValueEx(key, "TimeZoneKeyName")
                    offset, _ = winreg.QueryValueEx(key, "Bias")
                    zone = str(zone).strip("\x00")  # thanks to tzlocal
                    offset = int(offset)
                    return SysTzInfo(zone, offset)
        except OSError:
            logger.debug("Failed getting info from Windows registry", exc_info=True)
        return None


__all__ = [
    "Clock",
    "ClockInfo",
    "ClockTime",
    "NtpClockType",
    "NtpContinents",
    "NtpTime",
    "SysTzInfo",
    "TzUtils",
]
