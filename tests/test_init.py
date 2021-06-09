import pytest

from suretime import TzMap


class TestInit:
    def test(self):
        assert TzMap.primary_zone("Europe/Tiraspol") == "Europe/Tiraspol"
        assert TzMap.primary_zone("Central Pacific Standard Time") == "Pacific/Guadalcanal"
        assert TzMap.primary_zone("Central Pacific Standard Time", "AQ") == "Antarctica/Casey"


if __name__ == "__main__":
    pytest.main()
