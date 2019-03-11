import collections
import itertools
import logging
import lxml.html
import requests


logger = logging.getLogger(__name__)


class Schedule:
    def __init__(self, schedule_html):
        self.html = schedule_html
        self.departments = _parse_departments(self.html)
        self.sections = _parse_sections(self.html)
        self.courses = _extract_courses(self.sections)

    @classmethod
    def fetch(cls, validterm):
        return cls(_fetch_schedule_page(validterm))

    @classmethod
    def fetch_latest(cls):
        latest_validterm = fetch_validterms()[-1]
        return cls.fetch(latest_validterm)


def fetch_validterms():
    course_search_page = requests.get(
        'https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.p_selectsubject'
    ).content
    document = lxml.html.fromstring(course_search_page)
    return [
        button.get('value')
        for button in document.cssselect('input[name="validterm"]')
    ]


def _fetch_schedule_page(validterm):
    return requests.post(
        'https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.P_ViewSchedule',
        data={
            'validterm': validterm,
            'subjcode': 'ALL',
            'openclasses': 'N'
        }
    ).text


def _parse_departments(schedule_page):
    document = lxml.html.fromstring(schedule_page)
    tables = document.cssselect('table.datadisplaytable')

    def get_department_code(table):
        FIRST_COURSE_ROW = 1
        DEPARTMENT_ID_COLUMN = 1
        department_id_cell = table[FIRST_COURSE_ROW][DEPARTMENT_ID_COLUMN]
        # Example text_content(): 'ANTH-001-01'
        return department_id_cell.text_content().split('-')[0]

    def get_department_name(table):
        # Department class table is always immediately preceded by a h3 with the
        # department's full name
        return table.getprevious().text_content()

    return {
        get_department_code(table): get_department_name(table)
        for table in tables
    }


def _parse_sections(schedule_page):
    document = lxml.html.fromstring(schedule_page)
    tables = document.cssselect('table.datadisplaytable')

    def is_class_row(row):
        # Course title cells ALWAYS have the 'rowspan' attribute
        TITLE_COLUMN = 2
        return row[TITLE_COLUMN].get('rowspan')

    all_rows = (row for table in tables for row in table)
    class_rows = filter(is_class_row, all_rows)

    sections = []
    for r in class_rows:
        try:
            sections.append(_row_to_section(r))
        except Exception:
            logger.exception('Could not parse:\n%s', lxml.html.tostring(r))
    return sections


def _extract_courses(sections):
    # tuple for hashability, namedtuple for convenience
    Course = collections.namedtuple('Course',
        ('department_code', 'course_number', 'title', 'units', 'notes'))

    def coursify(section):
        return Course._make([section[f] for f in Course._fields])

    # set guarantees uniqueness
    return {
        coursify(s)
        for s in sections
    }


def _row_to_section(row):
    def get_text(cell):
        return cell.text_content()

    def get_number(cell):
        try:
            return int(cell.text_content())
        except ValueError:
            return 0

    def reject(cell):
        return None

    def fieldify_department_id(cell):
        subfields = cell.text_content().split('-')
        return {
            'department_code': subfields[0],
            'course_number': subfields[1],
            'section': subfields[2],
        }

    def fieldify_title(cell):
        textLines = list(cell.itertext())

        # There are multi-line title cells with a rowspan of 1, unfortunately
        # That includes the case where the other line is a "Must Also Register"
        # AND includes the case where the other line is like, a subtitle, e.g.
        # "Journal Club\nCardiovascular Tissue Engineering"
        # if cell.get('rowspan') == '1' or len(textLines) == '1':
        #     return '\n'.join(textLines)
        # So the following is the safest:
        if len(textLines) == '1':
            return textLines
        else:
            return {
                'title': textLines[0],
                'notes': ''.join(textLines[1:])
            }

    def fieldify_days(cell):
        return cell.text_content()

    def fieldify_time(cell):
        time_text = cell.text_content()
        if 'TBD' in time_text:
            return {'start_time': 'TDB', 'end_time': 'TDB'}

        def to_minutes(time_string):
            hours, minutes = time_string.split(':')
            return int(hours) * 60 + int(minutes)

        raw_start, raw_end = time_text.split('-')
        start = to_minutes(raw_start)
        end = to_minutes(raw_end[:-2])
        if raw_end[-2:] == "pm" and not (to_minutes('12:00') <= end <= to_minutes('12:59')):
            if start < end:
                start += 12 * 60
            end += 12 * 60

        def to_time_string(time):
            return '{}:{} {}'.format(
                str(time // 60 % 12 or 12), # circuit to 12 if % 12 == 0
                str(time % 60 or '00'), # circuit to '00' if % 60 == 0
                ('PM' if time >= to_minutes('12:00') else 'AM')
            )

        return {'start_time': to_time_string(start), 'end_time': to_time_string(end)}

    COLUMN_TRANSFORM_PAIRS = (
        ('CRN', get_number),
        ('department_id', fieldify_department_id),
        ('title', fieldify_title),
        ('units', get_number),
        ('activity', get_text),
        ('days', fieldify_days),
        ('time', fieldify_time),
        ('location', get_text),
        ('term_length', reject),
        ('instructor', get_text),
        ('max_seats', get_number),
        ('taken_seats', get_number),
        ('free_seats', get_number)
    )

    def slice_pairs(pairs):
        # transpose, as per https://stackoverflow.com/questions/12974474/how-to-unzip-a-list-of-tuples-into-individual-lists
        return zip(*pairs)

    section = {
        key: transform(cell)

        for cell, key, transform
        in zip(row, *slice_pairs(COLUMN_TRANSFORM_PAIRS))
        if transform is not reject
    }

    # Flatten 1 level deep (the only level of nesting possible)
    flat_section = {}
    for k_out, v_out in section.items():
        if isinstance(v_out, collections.MutableMapping):
            for k_in, v_in in v_out.items():
                flat_section[k_in] = v_in
        else:
            flat_section[k_out] = v_out

    return flat_section
