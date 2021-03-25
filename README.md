# Ensure Timezone

[![Version status](https://img.shields.io/pypi/status/suretime)](https://pypi.org/project/suretime)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python version compatibility](https://img.shields.io/pypi/pyversions/suretime)](https://pypi.org/project/suretime)
[![Version on GithHb](https://img.shields.io/github/v/release/dmyersturnbull/suretime?include_prereleases&label=GitHub)](https://github.com/dmyersturnbull/suretime/releases)
[![Version on PyPi](https://img.shields.io/pypi/v/suretime)](https://pypi.org/project/suretime)
[![Build (Github Actions)](https://img.shields.io/github/workflow/status/dmyersturnbull/suretime/Build%20&%20test?label=Build%20&%20test)](https://github.com/dmyersturnbull/suretime/actions)
[![Test coverage (coveralls)](https://coveralls.io/repos/github/dmyersturnbull/suretime/badge.svg?branch=main&service=github)](https://coveralls.io/github/dmyersturnbull/suretime?branch=main)
[![Maintainability (Code Climate)](https://api.codeclimate.com/v1/badges/2fbbf51ddb15e26f63f6/maintainability)](https://codeclimate.com/github/dmyersturnbull/suretime/maintainability)
[![Code Quality (Scrutinizer)](https://scrutinizer-ci.com/g/dmyersturnbull/suretime/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/dmyersturnbull/suretime/?branch=main)
[![Created with Tyrannosaurus](https://img.shields.io/badge/Created_with-Tyrannosaurus-0000ff.svg)](https://github.com/dmyersturnbull/tyrannosaurus)

Get IANA timezones and fully resolved timestamps, even on Windows.

Timestamps are resolved as accurately as the system permits.
Downloads and caches an up-to-date timezone name map if necessary.
You can map between zone names and find your local IANA zone.
Timezone-resolved datetimes and intervals know both real and calendar times, correctly representing
the ground truth even if a timezone shift occurs between events – such as from a daylight savings change
or user boarding a flight. 

To install: `pip install suretime`. For platform independence, also install `tzdata==2020.5`.
[See the docs 📚](https://suretime.readthedocs.io/en/stable/) for more info.
A few examples:

```python
from suretime import tz_map, datetime

# Get your local system, non-IANA timezone
system_time = datetime.now().astimezone()
system_timezone = system_time.tzname()

# Get an IANA timezone instead:
tz_map.local_primary_zone()  # ............ | ZoneInfo[America/Los_Angeles]
# Or for an arbitrary system timezone name:
tz_map.primary(system_timezone)  # ............ | ZoneInfo[America/Los_Angeles]
# Of course, it maps IANA zones to themselves:
tz_map.primary("America/Los_Angeles")  # ............ | ZoneInfo[America/Los_Angeles]

# Get all IANA timezones that could match a zone
tz_map.get_zones_with_territory("Russia Time Zone 3", "UA")  # | ZoneInfo["Europe/Samara"]

# Get a fully resolved "tagged datetime"
# It contains:
# - The zoned datetime
# - The primary IANA ZoneInfo
# - The original system timezone
# - A system wall time (`time.monotonic_ns`)
tagged = tz_map.tagged_local_datetime(datetime.now())  # ..... | TaggedDatetime[ ... ]

# Compare tagged datetimes
print(tagged < tagged)  # .................... | False
print(tagged == tagged)  # .................... | True: They're the same point in time
print(tagged == system_time)  # .................... | True: They're the same point in time
print(tagged.is_identical_to(tagged))  # .................... | True: They're exactly the same
# "2021-01-20T22:24:13.219253-07:00 [America/Los_Angeles]" :
print(tagged.iso_with_zone)

# Get a "tagged duration" with the start and end, and monotonic real time in nanoseconds
then = tz_map.tagged_now()  # .............. | TaggedDatetime [ ... ]
for i in list(range(10000)): i += 1  # .............. | Just waiting a little
now = tz_map.tagged_now()  # .............. | TaggedInterval [ ... ]
interval = tz_map.tagged_interval(then, now)  # .............. | TaggedInterval [ ... ]
print(interval.delta_real_time)  # .............. | Actual time passed
print(interval.delta_calendar_time)  # .............. | Simple end - start
print(interval.exact_duration_str)  # .............. | days:HH:mm:ss.millis.micros.nanos
```

Licensed under the terms of the [Apache License 2.0](https://spdx.org/licenses/Apache-2.0.html).
[New issues](https://github.com/dmyersturnbull/suretime/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/dmyersturnbull/suretime/blob/main/CONTRIBUTING.md)
and [security policy](https://github.com/dmyersturnbull/suretime/blob/main/SECURITY.md).

Generated with [Tyrannosaurus](https://github.com/dmyersturnbull/tyrannosaurus).
