# SPDX-FileCopyrightText: Copyright 2021-2023, Contributors to Suretime
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/suretime
# SPDX-License-Identifier: Apache-2.0

import pytest

from suretime._clock import NtpClockType, TzUtils


class TestInit:
    def test_ntp(self):
        v = TzUtils.get_ntp_clock("north-america", NtpClockType.client_received)
        assert v.clock.name == "north-america:client-received"

    def test_sys(self):
        v = TzUtils.get_sys_zone()
        assert v.zone_name is not None

    def test_etc(self):
        v = TzUtils.get_offset_zone()
        assert v.zone_name.startswith("Etc/")


if __name__ == "__main__":
    pytest.main()
