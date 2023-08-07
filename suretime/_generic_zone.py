# SPDX-FileCopyrightText: Copyright 2021-2023, Contributors to Suretime
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/suretime
# SPDX-License-Identifier: Apache-2.0

"""
Model classes for suretime.

Model and utility classes for suretime.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, AbstractSet, FrozenSet, Optional

if TYPE_CHECKING:
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
    territory: str | None
    ianas: frozenset[ZoneInfo]

    @classmethod
    def of(
        cls,
        name: str,
        territory: str | None = "primary",
        ianas: AbstractSet[ZoneInfo] | None = None,
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
