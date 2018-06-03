# UCMercedule: Scraper
A Python module that scrapes [UC Merced class schedules][1] for you!

Just create a `Schedule` object with `scraper.Schedule(validterm)`, where `validterm` is a value from the eponymous radio button group found in the [UC Merced Schedule Search form][1]. Call `scraper.fetchValidterms()` to get the current `validterm`s, or inspect the search page's raw source HTML.

## Example usage
```python
import json
import pathlib # Python 3.5+; for pre3.5 Python, import pathlib2
import scraper

pathlib.Path('./example').mkdir(exist_ok=True)

# Fall Semester 2018
# schedule = scraper.Schedule(201830)

validterms = scraper.fetchValidterms()
schedule = scraper.Schedule(validterms[-1]) # latest term

with open('example/Fall_2018_Schedule.html', 'wb') as f:
    f.write(schedule.html)
with open('example/Fall_2018_Departments.json', 'w') as f:
    json.dump(schedule.departments, f, sort_keys=True, indent=4)
with open('example/Fall_2018_Classes.json', 'w') as f:
    json.dump(schedule.classes, f, sort_keys=True, indent=4)
```
Check out the resulting schedule files in the [example folder](example/).

[1]: https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.p_selectsubject