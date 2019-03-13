from collections import namedtuple, OrderedDict, MutableMapping
import itertools
import logging
import lxml.html
import requests


logger = logging.getLogger(__name__)


class Schedule:
    def __init__(self, schedule_html, term):
        self.html = schedule_html
        self.term = term
        self.departments, self.courses, self.sections = _parse_tables(self.html)
    
    @classmethod
    def fetch(cls, term):
        return cls(_fetch_schedule_page(term.code), term)

    @classmethod
    def fetch_latest(cls):
        def get_last_value(ordered_dict):
            return next(reversed(ordered_dict.values()))
        return cls.fetch(get_last_value(get_terms()))


def get_terms():
    if get_terms.terms is None:
        get_terms.terms = _fetch_terms()
    return get_terms.terms
get_terms.terms = None


def _fetch_terms():
    course_search_page = requests.get(
        'https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.p_selectsubject'
    ).content
    document = lxml.html.fromstring(course_search_page)

    """
    In the schedule search form, each term line is a <tr>, e.g.:
    <tr>
        <td class="pldefault">
            <input type="radio" name="validterm" value="201930" checked="">
        </td>
        <td class="pldefault">Fall Semester 2019</td>
    </tr>
    """
    Term = namedtuple('Term', ['code', 'name'])
    def code(button):
        return button.get('value')

    return OrderedDict([
        (
            code(button),
            Term(code(button), button.getparent().getnext().text_content())
        )
        for button in document.cssselect('input[name="validterm"]')
    ])


def _fetch_schedule_page(code):
    return requests.post(
        'https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.P_ViewSchedule',
        data={
            'validterm': code,
            'subjcode': 'ALL',
            'openclasses': 'N'
        }
    ).text


def _parse_departments(tables):
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

    return OrderedDict([
        (get_department_code(table), get_department_name(table))
        for table in tables
    ])


def _parse_tables(schedule_page):
    document = lxml.html.fromstring(schedule_page)
    tables = document.cssselect('table.datadisplaytable')

    departments = _parse_departments(tables)

    def is_class_row(row): # as opposed to an EXAM row
        # Course title cells ALWAYS have the 'rowspan' attribute
        TITLE_COLUMN = 2
        return row[TITLE_COLUMN].get('rowspan')

    all_rows = (row for table in tables for row in table)
    class_rows = filter(is_class_row, all_rows)

    # Convert rows to section dicts
    sections = []
    for r in class_rows:
        try:
            s = _row_to_section(r)
        except Exception:
            logger.exception('Could not parse:\n%s', lxml.html.tostring(r))
        else:
            sections.append(s)

    # Extract courses before sections are purged of Course-only fields
    courses = _extract_courses(sections)

    for s in sections:
        # keep only department_code, course_number, and title (foreign keys on Courses)
        del s['units']
    Section = namedtuple('Section', sections[0].keys())
    def sectionify(s):
        return Section(*[s[f] for f in Section._fields])

    return departments, courses, tuple([sectionify(s) for s in sections])


def _extract_courses(sections):
    # department_code, number, and title make up the composite primary key
    Course = namedtuple('Course',
        ('department_code', 'number', 'title', 'units')) # note that it's 'number', not 'course_number' as it is in sections

    def coursify(section):
        # convert 'course_number' to 'number'
        values = [section[f] for f in Course._fields if f != 'number']
        values.insert(Course._fields.index('number'), section['course_number'])
        return Course(*values)

    # use OrderedDict instead of set to guarantee order and, by  exploiting the
    # uniqueness of keys in dicts, to guarantee course uniqueness
    courses_as_keys = OrderedDict([
        (coursify(s), None) # courses stored as keys for aforementioned behavior; associated value does not matter
        for s in sections
        # Do not make courses out of unitless sections (which would otherwise
        # get their own course in this set because the 0-units would make a
        # unique identity) UNLESS the unitless section is a main (i.e.
        # not supplementary DISC or LAB) section
        if s['units'] > 0 or s['activity'] not in ('DISC', 'LAB')
    ])

    return tuple(courses_as_keys.keys())


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
        return OrderedDict([
            ('department_code', subfields[0]),
            ('course_number', subfields[1]),
            ('number', subfields[2])
        ])

    def fieldify_title(cell):
        textLines = list(cell.itertext())

        # There are multi-line title cells with a rowspan of 1, unfortunately
        # That includes the case where the other line is a "Must Also Register"
        # AND includes the case where the other line is like, a subtitle, e.g.
        # "Journal Club\nCardiovascular Tissue Engineering"
        # if cell.get('rowspan') == '1' or len(textLines) == '1':
        #     return '\n'.join(textLines)
        # So the following is the safest:
        if len(textLines) == 1:
            return {
                'title': textLines[0],
                'notes': tuple()
            }
        else:
            result = {
                'title': textLines[0],
                'notes': [s.title() for s in textLines[1:]]
            }

            # Distinguish sub-title from note info
            if not result['notes'][0].startswith(('Must ', 'Class ')):
                result['title'] += '\n' + result['notes'][0]
                result['notes'].pop(0)

            result['notes'] = tuple(result['notes'])
            return result


    def fieldify_time(cell):
        time_text = cell.text_content()
        if 'TBD' in time_text:
            return OrderedDict([('start_time', 'TBD'), ('end_time', 'TBD')])

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

        return OrderedDict([('start_time', to_time_string(start)), ('end_time', to_time_string(end))])

    COLUMN_TRANSFORMS = (
        ('CRN', get_number),
        ('department_id', fieldify_department_id),
        ('title', fieldify_title),
        ('units', get_number),
        ('activity', get_text),
        ('days', get_text),
        ('time', fieldify_time),
        ('location', get_text),
        ('term_length', reject),
        ('instructor', get_text),
        ('max_seats', get_number),
        ('taken_seats', get_number),
        ('free_seats', get_number)
    )

    def transpose(pairs):
        # Per https://stackoverflow.com/a/12974504
        return zip(*pairs)

    section = OrderedDict([
        (key, transform(cell))

        for cell, key, transform
        in zip(row, *transpose(COLUMN_TRANSFORMS))
        if transform is not reject
    ])

    # make new dict with dict-value fields merged in
    flat_section = OrderedDict()
    for k, v in section.items():
        if isinstance(v, MutableMapping):
            for k_in, v_in in v.items():
                flat_section[k_in] = v_in
        else:
            flat_section[k] = v

    return flat_section
