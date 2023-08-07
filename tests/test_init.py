# SPDX-FileCopyrightText: Copyright 2021-2023, Contributors to Suretime
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/suretime
# SPDX-License-Identifier: Apache-2.0

import pytest

import suretime


class TestInit:
    def test_zones(self):
        assert str(suretime.zone.only("Europe/Tiraspol")) == "Europe/Tiraspol"
        assert str(suretime.zone.only("Central Pacific Standard Time")) == "Pacific/Guadalcanal"
        assert str(suretime.zone.only("Central Pacific Standard Time", "AQ")) == "Antarctica/Casey"

    def test_ntp(self):
        t = suretime.clock.ntp()
        assert t.clock.name == "north-america:client-sent"
        assert t.clock.info.is_ntp
        assert t.clock.info.is_epoch
        assert t.nanos > 0


if __name__ == "__main__":
    pytest.main()
