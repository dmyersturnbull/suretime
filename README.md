# Ensure Timezone

[![Version status](https://img.shields.io/pypi/status/ensuretimezone)](https://pypi.org/project/ensuretimezone)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python version compatibility](https://img.shields.io/pypi/pyversions/ensuretimezone)](https://pypi.org/project/ensuretimezone)
[![Version on Docker Hub](https://img.shields.io/docker/v/dmyersturnbull/ensuretimezone?color=green&label=Docker%20Hub)](https://hub.docker.com/repository/docker/dmyersturnbull/ensuretimezone)
[![Version on Github](https://img.shields.io/github/v/release/dmyersturnbull/ensuretimezone?include_prereleases&label=GitHub)](https://github.com/dmyersturnbull/ensuretimezone/releases)
[![Version on PyPi](https://img.shields.io/pypi/v/ensuretimezone)](https://pypi.org/project/ensuretimezone)
[![Documentation status](https://readthedocs.org/projects/ensuretimezone/badge)](https://ensuretimezone.readthedocs.io/en/stable)
[![Build (Github Actions)](https://img.shields.io/github/workflow/status/dmyersturnbull/ensuretimezone/Build%20&%20test?label=Build%20&%20test)](https://github.com/dmyersturnbull/ensuretimezone/actions)
[![Test coverage (coveralls)](https://coveralls.io/repos/github/dmyersturnbull/ensuretimezone/badge.svg?branch=main&service=github)](https://coveralls.io/github/dmyersturnbull/ensuretimezone?branch=main)
[![Maintainability (Code Climate)](https://api.codeclimate.com/v1/badges/<<apikey>>/maintainability)](https://codeclimate.com/github/dmyersturnbull/ensuretimezone/maintainability)
[![Code Quality (Scrutinizer)](https://scrutinizer-ci.com/g/dmyersturnbull/ensuretimezone/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/dmyersturnbull/ensuretimezone/?branch=main)

Get IANA timezones and fully resolved timestamps, even on Windows.

To install: `pip install ensuretimezone`. For platform independence, also install `tzdata==2020.5`.

Examples:

```python
from ensuretimezone import tz_map, datetime

# Get your local system, non-IANA timezone
system_time = datetime.now().astimezone()
system_timezone = system_time.tzname()

# Get an IANA timezone instead:
tz_map.local_primary_zone()  # .................................... ZoneInfo[America/Los_Angeles]
# Or for an arbitrary system timezone name:
tz_map.primary(system_timezone)  # ................................ ZoneInfo[America/Los_Angeles]
# Of course, it maps IANA zones to themselves:
tz_map.primary("America/Los_Angeles")  # .......................... ZoneInfo[America/Los_Angeles]

# Get all IANA timezones that could match a zone
tz_map.get_zone_with_territory("Russia Time Zone 3", "UA")  # ..... ZoneInfo["Europe/Samara"]

# Get a fully resolved "tagged datetime" with the original system timezone, the primary IANA ZoneInfo, and wall time
tagged = tz_map.tagged_local_datetime(datetime.now())  # .......... TaggedDatetime[ ... ]

# Compare tagged datetimes
print(tagged < tagged)                  # False
print(tagged == tagged)                 # True: They point to the same time
print(tagged == system_time)            # True: They point to the same time
print(tagged.is_identical_to(tagged))   # True: They're exactly the same (including the original system timezone)
print(tagged.iso_with_zone)             # "2021-01-20T22:24:13.219253-07:00 [America/Los_Angeles]"

# Get a "tagged duration" that contains the fully resolved start and end, and monotonic wall time in nanoseconds
then = tz_map.tagged_now()
for i in list(range(10000)): i += 1
now = tz_map.tagged_now()
ns = tz_map.tagged_duration(then, now).n_nanos  #  e.g. 162000
```

[See the docs 📚](https://ensuretimezone.readthedocs.io/en/stable/) for more info.

Licensed under the terms of the [Apache License 2.0](https://spdx.org/licenses/agpl3.html).
[New issues](https://github.com/dmyersturnbull/ensuretimezone/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/dmyersturnbull/ensuretimezone/blob/main/CONTRIBUTING.md)
and [security policy](https://github.com/dmyersturnbull/ensuretimezone/blob/main/SECURITY.md).  
Generated with [Tyrannosaurus](https://github.com/dmyersturnbull/tyrannosaurus).
