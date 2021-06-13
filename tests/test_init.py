import pytest

from suretime import Suretime


class TestInit:
    def test(self):
        assert str(Suretime.zones.only("Europe/Tiraspol")) == "Europe/Tiraspol"
        assert str(Suretime.zones.only("Central Pacific Standard Time")) == "Pacific/Guadalcanal"
        assert str(Suretime.zones.only("Central Pacific Standard Time", "AQ")) == "Antarctica/Casey"


if __name__ == "__main__":
    pytest.main()
