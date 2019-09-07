# UCMercedule: Scraper
A Python module that scrapes [UC Merced class schedules][1] for you!

## Installation
```
pipenv install ucmscraper
```

## Example usage
```python
import json
import pathlib
import ucmscraper

# Create example folder to store output files
pathlib.Path('./example').mkdir(exist_ok=True)

schedule = ucmscraper.Schedule.fetch_latest()

# used to serialize the namedtuples as .json files
class NamedTupleIterEncoder(json.JSONEncoder):
def default(self, o):
return [t._asdict() for t in o]

term = schedule.term.name
with open('example/{}.html'.format(term), 'w') as f:
f.write(schedule.html)
# OrderedDicts don't need sort_keys=True
with open('example/{} - Departments.json'.format(term), 'w') as f:
json.dump(schedule.departments, f, indent=4)
with open('example/{} - Courses.json'.format(term), 'w') as f:
json.dump([t._asdict() for t in schedule.courses], f, indent=4)
with open('example/{} - Sections.json'.format(term), 'w') as f:
json.dump([t._asdict() for t in schedule.sections], f, indent=4)
```
Check out the resulting schedule files in the [example folder](example/).

## API
Using this module pretty much just entails 1. creating a Schedule instance and
2. reading its data attributes; see below for more details.

### `ucmscraper.Schedule`
A `Schedule` instance object is a fully parsed UC Merced schedule page from a
given term.

The `Schedule` class is a [record type/plain old data structure][4], meaning it 
really only structures data into fields and provides very little functionality
on its own. The `Term`, `Course`, and `Section` classes that compose `Schedule`
follow the same vein. It is up to the client to implement their own functions
for handling these types.

`Schedule`s can created in three ways: two involve a factory class method, and
one is a plain constructor.

#### 1. `ucmscraper.Schedule.fetch_latest()`
Performs an HTTP request and, if successful, returns a Schedule object for the
latest term (Fall 2019 at the time of writing).

#### 2. `ucmscraper.Schedule.fetch(term)`
Performs an HTTP request and, if successful, returns a Schedule object for the
given `Term` object. `Term`s should be retrieved via
`ucmscraper.get_current_terms()`.

#### 3. `ucmscraper.Schedule(schedule_html)`
Parses `schedule_html` and returns a Schedule object.

#### Attributes
Schedule has the following data attributes:

`schedule.html` - a string of the raw HTML of the original schedule page

`schedule.term` - a `Term` object containing information about the term
associated with this `Schedule` instance.

`schedule.departments` - an [OrderedDict][2] whose keys are department codes and
whose values are the associated department titles, e.g.:
```
{
    'ANTH': 'Anthropology',
    'BEST': 'Bio Engin Small Scale Tech',
    'BIO': 'Biological Sciences',
    'BIOE': 'Bioengineering',
    ...
}
```
Keys follow the order that they appear in schedule pages, which is alphabetical.

`schedule.courses` - a tuple of `Course` [namedtuples](3) in the order that
courses appear on the schedule page, e.g.
```
(
    Course(
        department_code='ANTH',
        number='001',
        title='Sociocultural Anthropology',
        units=4
    ),
    ...
    Course(
        department_code='WRI',
        number='131C',
        title='Undergraduate Research Journal',
        units=2
    )
)
```

`schedule.sections` - a tuple of `Section` [namedtuples](3), each representing
one non-exam row from the schedule page, and in the order that sections appear
on the schedule page, e.g.:
```
(
    Section(
        CRN=30250,
        department_code='ANTH',
        course_number='001',
        number='01',
        title='Sociocultural Anthropology',
        notes=('Must Also Register For A Corresponding Discussion',),
        activity='LECT',
        days='MW',
        start_time='1:30 PM',
        end_time='2:45 PM',
        location='ACS 120',
        instructor='DeLugan, Robin',
        max_seats=210,
        taken_seats=0,
        free_seats=210
    ),
    ...
    Section(
        CRN=34978,
        department_code='WRI',
        course_number='131C',
        number='01',
        title='Undergraduate Research Journal',
        notes=(),
        activity='SEM',
        days='W',
        start_time='9:30 AM',
        end_time='11:20 AM',
        location='CLSSRM 272',
        instructor='Staff',
        max_seats=20,
        taken_seats=0,
        free_seats=20
    )
)
```

### `ucmscraper.get_current_terms()`
When first called, performs an HTTP request and if successful, returns a tuple
of terms currently available for viewing via the [official schedule search form][1].
Terms are represented by `Term` objects. Keys follow the same order as in the
official schedule search form.

Example return value:
```
(Term(code='201910', name='Spring Semester 2019'),
 Term(code='201920', name='Summer Semester 2019 - All Courses'),
 Term(code='201920 - S6', name='Summer Semester 2019 - First 6-week Summer Session A'),
 Term(code='201920 - S62', name='Summer Semester 2019 - Second 6-week Summer Session C'),
 Term(code='201920 - S8', name='Summer Semester 2019 - 8-week Summer Session B'),
 Term(code='201930', name='Fall Semester 2019'))
```

Note: old terms no longer on the official schedule search form have their access
restricted, so this module cannot retrieve them. I may maintain schedule pages
from old terms, so contact me if you want access to them. 

`Term` has the following data attributes:

`Term.code` - a string containing a `validterm` value from the
[official schedule search form][1]. When you choose a term via one of the
"Select a Term" radio buttons, you are selecting a `validterm` to be submitted
when you click "View Class Schedule".

`Term.name` - a string containing a term name associated with one of the
aforementioned radio buttons.

[1]: https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.p_selectsubject
[2]: https://docs.python.org/3.5/library/collections.html#collections.OrderedDict
[3]: https://docs.python.org/3.5/library/collections.html#collections.namedtuple
[4]: https://en.wikipedia.org/wiki/Record_(computer_science)
