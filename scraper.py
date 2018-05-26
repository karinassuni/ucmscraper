from lxml import etree
import requests

scheduleResponse = requests.post(
    'https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.P_ViewSchedule',
    data={
        'validterm': 201830,
        'subjcode': 'ALL',
        'openclasses': 'N'
    }
)
