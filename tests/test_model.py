from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from suretime._clock import Clock
from suretime._model import *


class TestModel:
    def test_parse(self):
        parsed = ZonedDatetime.parse("2011-11-04 00:11:22,001-07:00 [America/Los_Angeles]")
        assert parsed.iso_with_zone == "2011-11-04T00:11:22.001000-07:00 [America/Los_Angeles]"
        assert parsed.zone == ZoneInfo("America/Los_Angeles")
        assert parsed.utc.iso_with_zone == "2011-11-04T07:11:22.001000Z [Etc/UTC]"

    def test_offset(self):
        dt = ZonedDatetime.now_utc()
        assert dt.offset_str == "Z"
        dt = ZonedDatetime.now(ZoneInfo("America/Los_Angeles"))
        assert dt.offset_str == "−08:00"

    def test_add(self):
        dt0 = ZonedDatetime.now_utc()
        dt1 = dt0 + timedelta(hours=1)
        assert dt1.dt == dt0.dt + timedelta(hours=1)
        dt2 = dt1 - timedelta(hours=1)
        assert dt2.dt == dt0.dt

    def test_compare_zdt(self):
        dt0 = ZonedDatetime.now_utc()
        dt1 = dt0 + timedelta(hours=1)
        assert dt0 == dt0
        assert dt1 == dt1
        assert dt0 != dt1
        assert dt0 < dt1

    def test_eq_zdt(self):
        x = datetime.now().astimezone(timezone.utc)
        dt1 = ZonedDatetime.of(x, timezone.utc)
        dt2 = ZonedDatetime.of(x, timezone.utc, source=GenericTimezone.of("nope"))
        dt3 = ZonedDatetime.of(x, timezone.utc, source=GenericTimezone.of("other"))
        dt4 = ZonedDatetime.of(x, timezone.utc, source=GenericTimezone.of("other"))
        assert dt1 == dt2
        assert dt1 == dt3
        assert not dt1.is_identical_to(dt2)
        assert not dt1.is_identical_to(dt3)
        assert not dt2.is_identical_to(dt3)
        assert dt3.is_identical_to(dt4)

    def test_interval(self):
        x = datetime.now().astimezone(timezone.utc)
        y = x + timedelta(microseconds=15)
        start = TaggedDatetime.of(x, ZoneInfo("Etc/UTC"), 0, Clock.empty())
        end = TaggedDatetime.of(y, ZoneInfo("Etc/UTC"), 1000, Clock.empty())
        t = TaggedInterval(start, end)
        assert t.wall_nanos == 15000


if __name__ == "__main__":
    pytest.main()
