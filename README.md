# suretime

[![Version status](https://img.shields.io/pypi/status/suretime)](https://pypi.org/project/suretime)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python version compatibility](https://img.shields.io/pypi/pyversions/suretime)](https://pypi.org/project/suretime)
[![Version on GitHub](https://img.shields.io/github/v/release/dmyersturnbull/suretime?include_prereleases&label=GitHub)](https://github.com/dmyersturnbull/suretime/releases)
[![Version on PyPi](https://img.shields.io/pypi/v/suretime)](https://pypi.org/project/suretime)
[![Build (GitHub Actions)](https://img.shields.io/github/workflow/status/dmyersturnbull/suretime/Build%20&%20test?label=Build%20&%20test)](https://github.com/dmyersturnbull/suretime/actions)
[![Test coverage (coveralls)](https://coveralls.io/repos/github/dmyersturnbull/suretime/badge.svg?branch=main&service=github)](https://coveralls.io/github/dmyersturnbull/suretime?branch=main)
[![Maintainability (Code Climate)](https://api.codeclimate.com/v1/badges/14b23b28b0d9c37a0ebf/maintainability)](https://codeclimate.com/github/dmyersturnbull/suretime/maintainability)
[![Code Quality (Scrutinizer)](https://scrutinizer-ci.com/g/dmyersturnbull/suretime/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/dmyersturnbull/suretime/?branch=main)
[![Created with Tyrannosaurus](https://img.shields.io/badge/Created_with-Tyrannosaurus-0000ff.svg)](https://github.com/dmyersturnbull/tyrannosaurus)

Map nonstandard timezones to IANA zones on all platforms.
Record timestamps and intervals that behave correctly,
even if the timezone changes in the middle of a calculation.
`pip install suretime tzdata`.

### Timezone mapping

To get the local zone in IANA:

```python
import suretime
from datetime import datetime

datetime.now().tzname()  # "Pacific Standard Time"
suretime.zone.first_local()  # ZoneInfo[America/Los_Angeles])
```

To map a nonstandard zone from elsewhere:

```python
import suretime

suretime.zone.only("Europe/Tiraspol")  # ZoneInfo[Europe/Tiraspol]
suretime.zone.first("Central Pacific Standard Time")  # ZoneInfo[Pacific/Guadalcanal]
suretime.zone.first(
    "Central Pacific Standard Time", territory="AQ"
)  # ZoneInfo[Antarctica/Casey]
```

Note that there is no 1-1 mapping between Windows and IANA timezones,
so suretime can fail despite its name.

### "Tagged" datetimes and intervals

suretime also has models to represent timestamps and intervals as accurately as the system permits.
For example, a `TaggedInterval` contains the wall time, IANA zone, original (unmapped) timezone info
from the system, monotonic (typically boottime) clock time, and the clock used.

Timezone-resolved datetimes and intervals know both real and calendar times, correctly representing
the ground truth even if a timezone shift occurs between events – such as from a daylight savings change
or the user boarding a flight.

```python
import suretime

tagged = suretime.tag.now()
tagged.to_utc  # TaggedDateTime[...]
tagged.clock.name  # "boottime" on most systems
tagged == tagged  # same point in time
tagged.iso_with_zone  # "2021-01-20T22:24:13.219253-07:00 [America/Los_Angeles]"
```

### Comparison to [tzlocal](https://github.com/regebro/tzlocal)

tzlocal is a bit different. It:

- ... only handles your current system’s timezone
- ... is highly OS-specific
- ... requires many system calls, making it typically _much_ slower
- ... is compatible with Windows 2000, XP, and 7 and below
- ... is compatible with Python 3.6, 3.7, and 3.8
- ... very rarely, can access timezones on incorrectly configured POSIX systems

You can combine both packages, falling back to tzlocal if suretime fails.
(See the example below).

### Full example

```python
from datetime import datetime
import suretime

# Get your local system, non-IANA timezone
system_time = datetime.now().astimezone()
system_timezone = system_time.tzname()  # e.g. Pacific Standard Time

# Get an IANA timezone instead:
suretime.zone.only_local()  # ZoneInfo[America/Los_Angeles]
# Or for an arbitrary system timezone name:
suretime.zone.first(system_timezone)  # ZoneInfo[America/Los_Angeles]
# Of course, it maps IANA zones to themselves:
suretime.zone.only("America/Los_Angeles")  # ZoneInfo[America/Los_Angeles]

# Get all IANA timezones that could match a zone
# The first uses the primary/null territory
# The second uses the territory "AQ"
suretime.zone.all("Central Pacific Standard Time")  # {ZoneInfo[Pacific/Guadalcanal]}
suretime.zone.all("Central Pacific Standard Time", "AQ")  # {ZoneInfo[Antarctica/Casey]}

# Get 1 matching IANA zone; "get" means optional
suretime.zone.first("Central Pacific Standard Time", "AQ")  # ZoneInfo[Pacific/Casey]
suretime.zone.first("nonexistent zone")  # None
suretime.zone.only("nonexistent zone")  # errors
suretime.zone.only(
    "Central Pacific Standard Time", "any"
)  # fails (multiple possible IANA zones)

# Get a fully resolved "tagged datetime"
# It contains:
# - The zoned datetime
# - The primary IANA ZoneInfo
# - The original system timezone
# - A system wall time (`time.monotonic_ns`)
tagged = suretime.tag.now_local_sys()  # TaggedDatetime[ ... ]
print(tagged.clock.name)  # e.g. "boottime"
# or NTP:
tagged = suretime.tag.now_local_ntp(
    server="north-america", kind="server-received"
)  # TaggedDatetime[ ... ]
# or fully reliable but not keeping the local zone:
tagged = suretime.tag.now_utc_ntp()  # TaggedDatetime[ ... ]
# or NTP:
tagged = suretime.tag.now_local_sys()  # TaggedDatetime[ ... ]
print(tagged.clock.name)  # "ntp:..."
print(tagged.clock.info.resolution)  # e.g. -7

# 2021-01-20T22:24:13.219253-07:00 [America/Los_Angeles]
print(tagged.iso_with_zone)  # <datetime> [zone]
print(tagged.source.territory)  # "primary"

# if you only need the real time:
suretime.clock.sys()
# or:
suretime.clock.ntp()
# or for all of the NTP clock times:
ntp_data = suretime.clock.ntp_raw()
print(ntp_data.root_dispersion)
print(ntp_data.server_sent, ntp_data.client_received)
print(ntp_data.round_trip.total_seconds())

# Adjust a tagged time to a new real time
tagged = suretime.tag.now_utc_sys()  # TaggedDatetime[ ... ]
sys_now = suretime.clock.sys()
tagged.at(sys_now)
# now the datetime is adjusted to where it should be at the new real time

# Compare tagged datetimes
print(tagged < tagged)  # False
print(tagged == tagged)  # True: They're the same point in time
print(tagged == system_time)  # True: They're the same point in time
print(tagged.is_identical_to(tagged))  # True: They're exactly the same

# Get a "tagged duration" with the start and end, and monotonic real time in nanoseconds
then = suretime.tag.now()  # TaggedDatetime [ ... ]
for i in list(range(10000)):
    i += 1  # Just waiting a little
now = suretime.tag.now()  # TaggedInterval [ ... ]
interval = suretime.tag.interval(then, now)  # TaggedInterval [ ... ]
print(interval.real_delta)  # Actual time passed
print(interval.wall_delta)  # Simple end - start
print(interval.iso)  # start--end in ISO 8601 format
print(interval.real_str)  # days:HH:mm:ss.millis.micros.nanos
print(interval.duration.iso)  # e.g. P0Y3M5DT14H22M35.223051S

# use suretime, fall back to tzlocal
import tzlocal


def get_local() -> suretime.Types.TaggedDatetime:
    try:
        return suretime.tag.now()
    except suretime.Errors.CannotMapTzError:
        zone = tzlocal.get_localzone()
        return suretime.tag.exact(datetime.now(zone))
```

### 🍁 Contributing

Licensed under the terms of the [Apache License 2.0](https://spdx.org/licenses/Apache-2.0.html).
[New issues](https://github.com/dmyersturnbull/suretime/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/dmyersturnbull/suretime/blob/main/CONTRIBUTING.md)
and [security policy](https://github.com/dmyersturnbull/suretime/blob/main/SECURITY.md).

Generated with [Tyrannosaurus](https://github.com/dmyersturnbull/tyrannosaurus).
