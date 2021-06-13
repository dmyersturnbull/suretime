import pytest

from suretime._utils import TzUtils, NtpClockType


class TestInit:
    def test_ntp(self):
        v = TzUtils.get_ntp_time("north-america")
        v = TzUtils.get_ntp_clock("north-america", NtpClockType.client_received)
        assert v.clock.name == "north-america:client_received"

    def test_sys(self):
        v = TzUtils.get_sys_zone()
        assert v.zone_name is not None

    def test_etc(self):
        v = TzUtils.get_offset_zone()
        assert v.zone_name.startswith("Etc/")


if __name__ == "__main__":
    pytest.main()
