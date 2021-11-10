"""
Model classes for suretime.

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

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import AbstractSet, FrozenSet, Optional
from zoneinfo import ZoneInfo


@dataclass(frozen=True, repr=True, order=True)
class GenericTimezone:
    """
    A generic timezone that matches zero or more IANA timezones.
    Contains the source zone (e.g. America/Los_Angeles or Mountain Standard Time),
    along with the territory.

    Attributes:
        name: The name of the zone (e.g. Mountain Standard Time) or America/Los_Angeles
        territory: None for IANA zones, the 2-letter territory code,
                   or "primary" if the zone is missing
        ianas: set of IANA zones that match, sorted alphabetically by name
    """

    name: str
    territory: Optional[str]
    ianas: FrozenSet[ZoneInfo]

    @classmethod
    def of(
        cls,
        name: str,
        territory: Optional[str] = "primary",
        ianas: Optional[AbstractSet[ZoneInfo]] = None,
    ) -> GenericTimezone:
        if ianas is None:
            ianas = frozenset()
        return GenericTimezone(name, territory, frozenset(ianas))

    @cached_property
    def is_iana(self) -> bool:
        return len(self.ianas) == 1 and self.name == next(iter(self.ianas))

    @property
    def has_iana(self) -> bool:
        return len(self.ianas) > 0


__all__ = ["GenericTimezone"]
