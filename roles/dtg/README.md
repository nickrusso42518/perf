# role : dtg
This role collects the date/time group (DTG) from the
control machine and stores it in a variable called `DTG`.
This provides a simple time stamping method.

## Hosts
Typically this role is included in a play that only includes
the control machine (localhost). Collecting the DTG once and
applying it multiple times has two major benefits:

  * Every stamp is the same (not off by a few milliseconds)
  * Reduces execution time and processing load

## Role tasks (summarized)
This role runs the setup module and only collects the
date/time field in `iso8601_basic_short` format. This
format was chosen because it has no special characters.
An example output would be __"20180127T130500"__ and has
the following characteristics, which are validated with
the role regression test:
  * 8 digit date format: __YYYYMMDD__ for simple sorting/searching
  * The letter __"T"__ to specify the next field is the time of day
  * 6 digit time format: __HHMMSS__ in the UTC timezone
  * Total length is always exactly __15__ characters
