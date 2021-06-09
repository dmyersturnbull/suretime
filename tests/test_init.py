import pytest

from suretime import tz_map


class TestInit:
    def test(self):
        assert tz_map.primary_zone("Europe/Tiraspol") == "Europe/Tiraspol"
        assert tz_map.primary_zone("Central Pacific Standard Time") == "Pacific/Guadalcanal"
        assert tz_map.primary_zone("Central Pacific Standard Time", "AQ") == "Antarctica/Casey"


if __name__ == "__main__":
    pytest.main()
