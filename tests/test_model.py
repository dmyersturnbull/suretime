from zoneinfo import ZoneInfo

import pytest

from suretime._model import *


class TestModel:
    def test_parse(self):
        parsed = ZonedDatetime.parse("2011-11-04 00:11:22,001-07:00 [America/Los_Angeles]")
        assert parsed.iso_with_zone == "2011-11-04T00:11:22.001000-07:00 [America/Los_Angeles]"
        assert parsed.zone == ZoneInfo("America/Los_Angeles")
        assert parsed.utc.iso_with_zone == "2011-11-04T07:11:22.001000Z [Etc/UTC]"


if __name__ == "__main__":
    pytest.main()
