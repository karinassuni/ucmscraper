# UCMercedule: Scraper
A Python module that scrapes [UC Merced class schedules][1] for you!

## API
Using this module just entails 1. creating a Schedule instance and 2. reading
its data attributes; see below for more details.

### `class Schedule`
A `Schedule` instance object is a fully parsed UC Merced schedule page from a
given term.

`Schedule`s can created in three ways: two involve a "factory" class method, and
one is a plain constructor.

#### 1. `Schedule.fetch_latest()`
Performs an HTTP request and, if successful, returns a Schedule object for the
latest term (Fall 2018 at the time of writing).

#### 2. `Schedule.fetch(validterm)`
Performs an HTTP and, if successful, returns a Schedule object from the given
`validterm`.

A `validterm` is a form value associated with the "Select a Term" radio buttons
in the [official schedule search form][1].

#### 3. `Schedule(schedule_html)`
Parses `schedule_html` and returns a Schedule object.

#### Attributes
Each Schedule object has the following data attributes:

`schedule.html` - a string of the raw HTML of the original schedule page

`schedule.departments` - a dictionary whose keys are department codes and whose
values are the associated department titles, e.g.:
```
{
    'ANTH': 'Anthropology',
    'BEST': 'Bio Engin Small Scale Tech',
    'BIO': 'Biological Sciences',
    'BIOE': 'Bioengineering',
    ...
}
```

`schedule.sections` - a list of dictionaries each representing one non-exam row
from the schedule page, e.g.:
```
[
    {
        'CRN': '30973',
        'departmentCode': 'MATH',
        'courseNumber': '125',
        'section': '03D',
        'title': 'Intermediate Diff Eqs',
        'notes': [],
        'units': 0,
        'activity': 'DISC',
        'days': [4],
        'startTime': 810,
        'endTime': 860,
        'instructor': 'Staff',
        'maxSeats': 30,
        'takenSeats': 9,
        'freeSeats': 21
    },
    ...
]
```

### `ucmscraper.fetchValidterms()`
Performs an HTTP request and, if successful returns a list of all of the current
`validterm`s.

To get a hard-coded (read: non-updating) list of `validterm`s, you can inspect
the raw source HTML of [the official schedule search form][1].


## Installation
```
pipenv install ucmscraper
```

## Example usage
```python
import json
import pathlib # Python 3.5+; for pre3.5 Python, import pathlib2
import ucmscraper

pathlib.Path('./example').mkdir(exist_ok=True)

try:
    with open('example/Fall_2018_Schedule.html', 'r') as f:
        schedule_html = f.read()
        schedule = ucmscraper.Schedule(schedule_html)
except FileNotFoundError:
    schedule = ucmscraper.Schedule.fetch_latest()

with open('example/Fall_2018_Schedule.html', 'w') as f:
    f.write(schedule.html)
with open('example/Fall_2018_Departments.json', 'w') as f:
    json.dump(schedule.departments, f, sort_keys=True, indent=4)
with open('example/Fall_2018_Sections.json', 'w') as f:
    json.dump(schedule.sections, f, sort_keys=True, indent=4)
```
Check out the resulting schedule files in the [example folder](example/).

[1]: https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.p_selectsubject
