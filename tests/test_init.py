import pytest

from suretime import TzMap


class TestInit:
    def test(self):
        assert str(TzMap.zones.only("Europe/Tiraspol")) == "Europe/Tiraspol"
        assert str(TzMap.zones.only("Central Pacific Standard Time")) == "Pacific/Guadalcanal"
        assert str(TzMap.zones.only("Central Pacific Standard Time", "AQ")) == "Antarctica/Casey"


if __name__ == "__main__":
    pytest.main()
