import collections
import itertools
import lxml.html
import requests


class Schedule:
    def __init__(self, validterm):
        self.html = _fetchSchedulePage(validterm)
        self.departments = _parseDepartments(self.html)
        self.classes = _parseClasses(self.html)


def fetchValidterms():
    courseSearchPage = requests.get(
        'https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.p_selectsubject'
    ).content
    document = lxml.html.fromstring(courseSearchPage)
    return [
        button.get('value')
        for button in document.cssselect('input[name="validterm"]')
    ]


def _fetchSchedulePage(validterm):
    return requests.post(
        'https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.P_ViewSchedule',
        data={
            'validterm': validterm,
            'subjcode': 'ALL',
            'openclasses': 'N'
        }
    ).content


def _parseDepartments(schedulePage):
    root = lxml.html.fromstring(schedulePage)
    tables = root.cssselect('table.datadisplaytable')

    def getDepartmentCode(table):
        FIRST_COURSE_ROW = 1
        DEPARTMENT_ID_COLUMN = 1
        departmentIdCell = table[FIRST_COURSE_ROW][DEPARTMENT_ID_COLUMN]
        # Example text_content(): 'ANTH-001-01'
        return departmentIdCell.text_content().split('-')[0]

    def getDepartmentName(table):
        # Department class table is always immediately preceded by a h3 with the
        # department's full name
        return table.getprevious().text_content()

    return {
        getDepartmentCode(table): getDepartmentName(table)
        for table in tables
    }


def _parseClasses(schedulePage):
    root = lxml.html.fromstring(schedulePage)
    tables = root.cssselect('table.datadisplaytable')

    def isClassRow(row):
        # Course title cells ALWAYS have the 'rowspan' attribute
        TITLE_COLUMN = 2
        return row.getchildren()[TITLE_COLUMN].get('rowspan')

    allRows = (row for table in tables for row in table.getchildren())
    classRows = filter(isClassRow, allRows)

    return [_rowToClassMap(r) for r in classRows]


def _rowToClassMap(row):
    def getText(cell):
        return cell.text_content()

    def getNumber(cell):
        try:
            return int(cell.text_content())
        except ValueError:
            return 0

    def reject(cell):
        return None

    def fieldifyDepartmentID(cell):
        subfields = cell.text_content().split('-')
        return {
            'departmentCode': subfields[0],
            'courseNumber': subfields[1],
            'section': subfields[2],
        }

    def fieldifyTitle(cell):
        rowspan = cell.get('rowspan')
        textLines = list(cell.itertext())

        if rowspan == '1' or len(textLines) == '1':
            return '\n'.join(textLines)
        else:
            return {
                'title': textLines[0],
                'notes': textLines[1:]
            }

    def fieldifyDays(cell):
        DAYS = 'MTWRFS'
        dayText = cell.text_content()
        if dayText == '&nbsp':
            return ''
        else:
            return [DAYS.index(day) for day in dayText]

    def fieldifyTime(cell):
        timeText = cell.text_content()
        if 'TBD' in timeText:
            return 'TBD'

        def toMinutes(timeString):
            hours, minutes = timeString.split(':')
            return int(hours) * 60 + int(minutes)

        rawStart, rawEnd = timeText.split('-')
        start = toMinutes(rawStart)
        end = toMinutes(rawEnd[:-2])
        if rawEnd[-2:] == "pm" and not (toMinutes('12:00') <= end <= toMinutes('12:59')):
            if start < end:
                start += 12 * 60
            end += 12 * 60

        return {'startTime': start, 'endTime': end}

    COLUMNS_TRANSFORMS_MAP = {
        'CRN': getText,
        'departmentID': fieldifyDepartmentID,
        'title': fieldifyTitle,
        'units': getNumber,
        'activity': getText,
        'days': fieldifyDays,
        'time': fieldifyTime,
        'location': reject,
        'termLength': reject,
        'instructor': getText,
        'maxSeats': getNumber,
        'takenSeats': getNumber,
        'freeSeats': getNumber
    }

    class_ = {
        key: transform(cell)

        for cell, key, transform
        in zip(row.getchildren(), COLUMNS_TRANSFORMS_MAP.keys(), COLUMNS_TRANSFORMS_MAP.values())
        if transform is not reject
    }

    # Flatten 1 level deep (the only level of nesting possible)
    flatClass = {}
    for k_out, v_out in class_.items():
        if isinstance(v_out, collections.MutableMapping):
            for k_in, v_in in v_out.items():
                flatClass[k_in] = v_in
        else:
            flatClass[k_out] = v_out

    return flatClass
