import pytest

from suretime import Suretime


class TestInit:
    def test_zones(self):
        assert str(Suretime.zones.only("Europe/Tiraspol")) == "Europe/Tiraspol"
        assert str(Suretime.zones.only("Central Pacific Standard Time")) == "Pacific/Guadalcanal"
        assert str(Suretime.zones.only("Central Pacific Standard Time", "AQ")) == "Antarctica/Casey"

    def test_ntp(self):
        t = Suretime.clocks.ntp()
        assert t.clock.name == "north-america:client-sent"
        assert t.clock.info.is_ntp
        assert t.clock.info.is_epoch
        assert t.nanos > 0


if __name__ == "__main__":
    pytest.main()
