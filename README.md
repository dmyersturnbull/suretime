# Suretime

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

(Try to) get IANA timezones on Windows.
Get fully resolved timestamps and intervals and easily calculate properties.

Also see [tzlocal](https://github.com/regebro/tzlocal).
It sometimes does a better job of getting an IANA zone from your local system zone.
However, it only works for your local system zone and relies on OS system files
(both Unix and Windows), so it yields different results on different platforms.
In contrast, suretime is platform-invariant and a little more precise
(e.g. by considering territories), but will fail to map the local system zone
more often than tzlocal. Suretime also has useful model classes and is *much* faster.
If you don’t need the platform-invariance, combine both for the best results
(refer to the last section of the example).

Timestamps are resolved as accurately as the system permits.
Downloads and caches an up-to-date timezone name map if necessary.
You can map between zone names and find your local IANA zone.
Timezone-resolved datetimes and intervals know both real and calendar times, correctly representing
the ground truth even if a timezone shift occurs between events – such as from a daylight savings change
or user boarding a flight.
Note that there is no 1-1 mapping between Windows and IANA timezones.
There are several other limitations and [known issues](https://github.com/dmyersturnbull/suretime/issues).

To install: `pip install suretime tzdata`.
Examples:

```python
from suretime import TzMap, datetime

# Get your local system, non-IANA timezone
system_time = datetime.now().astimezone()
system_timezone = system_time.tzname()  # e.g. Pacific Standard Time

# Get an IANA timezone instead:
TzMap.zones.only_local()  # ZoneInfo[America/Los_Angeles]
# Or for an arbitrary system timezone name:
TzMap.zones.first(system_timezone)  # ZoneInfo[America/Los_Angeles]
# Of course, it maps IANA zones to themselves:
TzMap.zones.only("America/Los_Angeles")  # ZoneInfo[America/Los_Angeles]

# Get all IANA timezones that could match a zone
# The first uses the primary/null territory
# The second uses the territory "AQ"
TzMap.zones.all("Central Pacific Standard Time")  # {ZoneInfo[Pacific/Guadalcanal]}
TzMap.zones.all("Central Pacific Standard Time", "AQ")  # {ZoneInfo[Antarctica/Casey]}

# Get 1 matching IANA zone; "get" means optional
TzMap.zones.first("Central Pacific Standard Time", "AQ")  # ZoneInfo[Pacific/Casey]
TzMap.zones.first("nonexistent zone")  # None

# Get a fully resolved "tagged datetime"
# It contains:
# - The zoned datetime
# - The primary IANA ZoneInfo
# - The original system timezone
# - A system wall time (`time.monotonic_ns`)
tagged = TzMap.tagged.now()  # TaggedDatetime[ ... ]

# 2021-01-20T22:24:13.219253-07:00 [America/Los_Angeles]
print(tagged.iso_with_zone)  # <datetime> [zone]
print(tagged.source.territory)  # "primary"

# Compare tagged datetimes
print(tagged < tagged)  # False
print(tagged == tagged)  # True: They're the same point in time
print(tagged == system_time)  # True: They're the same point in time
print(tagged.is_identical_to(tagged))  # True: They're exactly the same

# Get a "tagged duration" with the start and end, and monotonic real time in nanoseconds
then = TzMap.tagged.now()  # TaggedDatetime [ ... ]
for i in list(range(10000)): i += 1  # Just waiting a little
now = TzMap.tagged.now()  # TaggedInterval [ ... ]
interval = TzMap.tagged.interval(then, now)  # TaggedInterval [ ... ]
print(interval.delta_real_time)  # Actual time passed
print(interval.delta_calendar_time)  # Simple end - start
print(interval.exact_duration_str)  # days:HH:mm:ss.millis.micros.nanos

# use suretime, fall back to tzlocal
import tzlocal

def get_local() -> TzMap.Types.TaggedDatetime:
  try:
    return TzMap.tagged.now()
  except TzMap.Errors.CannotMapTzError:
    zone = tzlocal.get_localzone()
    return TzMap.tagged.exact(datetime.now(zone))

```

Licensed under the terms of the [Apache License 2.0](https://spdx.org/licenses/Apache-2.0.html).
[New issues](https://github.com/dmyersturnbull/suretime/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/dmyersturnbull/suretime/blob/main/CONTRIBUTING.md)
and [security policy](https://github.com/dmyersturnbull/suretime/blob/main/SECURITY.md).

Generated with [Tyrannosaurus](https://github.com/dmyersturnbull/tyrannosaurus).
