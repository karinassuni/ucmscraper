import lxml.html
import requests

scheduleResponse = requests.post(
    'https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.P_ViewSchedule',
    data={
        'validterm': 201830,
        'subjcode': 'ALL',
        'openclasses': 'N'
    }
)

root = lxml.html.fromstring(scheduleResponse.content)

allRows = root.cssselect('table.datadisplaytable > tr')

COLUMNS = ('CRN', 'departmentID', 'title', 'units', 'activity', 'days', 'time', 'location', 'termLength', 'instructor', 'maxSeats', 'takenSeats', 'freeSeats')

def isHeader(row):
    return row.getchildren()[0].tag == 'th'

def isExamRow(row):
    return row.getchildren()[COLUMNS.index('activity')].text_content == 'EXAM'

classRows = filter(lambda r: not isHeader(r) and not isExamRow(r), allRows)
