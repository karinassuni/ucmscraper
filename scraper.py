import collections
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


def isHeader(row):
    return row.getchildren()[0].tag == 'th'


def isExamRow(row):
    ACTIVITY_COLUMN = 4
    return row.getchildren()[ACTIVITY_COLUMN].text_content == 'EXAM'


classRows = filter(lambda r: not isHeader(r) and not isExamRow(r), allRows)


def rowToClassMap(row):
    def getText(cell):
        return cell.text_content()

    def getNumber(cell):
        return int(cell.text_content())

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
        return [DAYS.index(day) for day in cell.text_content()]

    def fieldifyTime(cell):
        def toMinutes(timeString):
            hours, minutes = timeString.split(':')
            return int(hours) * 60 + int(minutes)

        rawStart, rawEnd = cell.text_content().split('-')
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
