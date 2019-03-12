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

`schedule.courses` - a set of `Course` [namedtuples](2), e.g.
```
{
    Course(
        department_code='ANTH',
        course_number='001',
        units=4,
        notes=('Must Also Register for a Corresponding Discussion')
    ),
    ...
}
```

`schedule.sections` - a list of `Section` [namedtuples](2) each representing one
non-exam row from the schedule page, e.g.:
```
[
    Section(
        CRN=30250,
        department_code='ANTH',
        course_number='001',
        section='01',
        activity='LECT',
        days='MW',
        start_time='1:30 PM',
        end_time='2:45 PM',
        location='ACS 120',
        instructor='DeLugan, Robin',
        max_seats=210,
        free_seats=210,
        taken_seats=0
    ),
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
import pathlib
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
[2]: https://docs.python.org/3.5/library/collections.html#collections.namedtuple