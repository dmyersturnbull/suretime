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

Code that reads and caches timezone mapping data.
"""

from __future__ import annotations
from datetime import datetime, timezone
import logging
import abc
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen
from typing import Mapping, Optional, FrozenSet, Sequence, Union
from zoneinfo import ZoneInfo, available_timezones

from suretime._model import TzMapType, TzDictType

logger = logging.getLogger("suretime")

import defusedxml.ElementTree as Xml

cldr_github_url = (
    "https://raw.githubusercontent.com/unicode-org/cldr/master/common/supplemental/windowsZones.xml"
)


class TzMapCacheEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FrozenSet):
            return list(obj)
        if isinstance(obj, ZoneInfo):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj


class TzMapCacheDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if isinstance(obj, dict):
            for key in list(obj):
                obj[key] = self.object_hook(obj[key])
            return obj
        if isinstance(obj, str):
            try:
                return datetime.fromisoformat(obj)
            except ValueError:
                return ZoneInfo(obj)
        if isinstance(obj, Sequence):
            return frozenset(obj)
        return obj


class TimezoneMapBackend(metaclass=abc.ABCMeta):
    def get(self) -> TzMapType:
        raise NotImplementedError()


@dataclass(frozen=True, repr=True)
class TimezoneMapFilesysCache(TimezoneMapBackend):
    path: Optional[Path] = None
    expiration_mins: int = 34560
    source_xml: Union[Path, str] = cldr_github_url

    def get(self) -> TzMapType:
        read = self._read()
        if read is not None:
            return read
        return self._save()

    def download(self) -> None:
        self._save()

    def _read(self) -> Optional[TzMapType]:
        if self.path is None or not self.path.exists():
            logger.debug(f"Timezone map cache not found at {self.path}. Generating.")
            return None
        txt = self.path.read_text(encoding="utf8")
        read = TzMapCacheDecoder().decode(txt)
        now = datetime.now(tz=timezone.utc)
        then = read["downloadTimestamp"]
        if (now - then).total_seconds() > self.expiration_mins * 60:
            logger.debug(f"Timezone map cache at {self.path} from {then} is expired. Regenerating.")
            return None
        logger.debug(f"Loaded timezone map cache at {self.path}")
        return read["mapping"]

    def _save(self) -> TzMapType:
        built = self._build()
        saved = dict(downloadTimestamp=datetime.now(tz=timezone.utc), mapping=built)
        encoded = TzMapCacheEncoder(ensure_ascii=False, allow_nan=False).encode(saved)
        if self.path is not None:
            self.path.write_text(encoded, encoding="utf8")
        return saved["mapping"]

    def _build(self) -> TzMapType:
        source = self._download()
        root = Xml.fromstring(source)
        zones = root.findall("windowsZones/mapTimezones/mapZone")
        mp: TzDictType = {}
        # First, map IANA zone names to themselves using 001 to mark as "primary"
        for tz in available_timezones():
            mp[tz] = {"001": frozenset([ZoneInfo(tz)])}
        # Then, map Windows zone names

        for node in zones:
            if node.tag == "mapZone":
                win_zone = node.attrib["other"]
                win_terr = node.attrib["territory"]
                iana_zones = [ZoneInfo(iana) for iana in node.attrib["type"].split(" ")]
                if win_zone not in mp:
                    mp[win_zone]: Mapping[str, ZoneInfo] = {}
                mp[win_zone][win_terr] = frozenset(iana_zones)
        return mp

    def _download(self) -> str:
        if isinstance(self.source_xml, str) and str(self.source_xml).startswith("https://"):
            with urlopen(self.source_xml) as f:  # nosec
                return f.read().decode("utf-8")
        return Path(self.source_xml).read_text(encoding="utf8")


__all__ = ["TimezoneMapBackend", "TimezoneMapFilesysCache"]
