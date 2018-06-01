# UCMercedule: Scraper
Scrape courses from [UC Merced's schedule pages][1].

## Example usage
```python
import json
import pathlib # Python 3.5+; import pathlib2 for pre-3.5 Python
import scraper

pathlib.Path('./example').mkdir(exist_ok=True)

html = scraper.fetchSchedulePage(201830)
with open('example/Fall_2018_Schedule.html', 'wb') as f:
    f.write(html)

classes = scraper.parseSchedulePage(html)
with open('example/Fall_2018_Schedule.json', 'w') as f:
    json.dump(classes, f, sort_keys=True, indent=4)
```
Check out the resulting schedule files in the [example folder](example/).

[1]: https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.p_selectsubject