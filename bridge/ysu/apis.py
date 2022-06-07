import requests
import xmltodict as xml
import aiohttp
from asgiref.sync import async_to_sync as a2s


async def async_get_username_by_school_id(school_id: str, timeout=5):
    # validate input data
    if len(school_id) != 12:
        return None

    # construct http request
    data = 'word=%s&index=4&currentPage=1&sql=stuSql&building=undefined&srtp_teacher_project_num=undefined&planyear=undefined' % school_id
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # get response
    timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post('http://202.206.243.8/StuExpbook/AutoCompleteServletSrtp',
                                data=data, headers=headers) as resp:
            if resp.status != 200:
                raise AssertionError('ysu-campus-server response status error: %d' % resp.status)
            data = await resp.text(encoding='utf8')
            print(data)

    # parse response
    data = xml.parse(data)
    data = data['words'].get('word')
    if data:
        if isinstance(data, str):
            _id, name = data.split('-')
            return name
        elif isinstance(data, list):
            data = [x.split('-') for x in data]
            id_to_name = {x[0]: x[1] for x in data}
            return id_to_name.get(school_id)


def get_username_by_school_id(id: str, timeout=5):
    return a2s(async_get_username_by_school_id)(id, timeout)


def request_auto_complete(school_id: str, page=1, index=4):
    url = 'http://202.206.243.8/StuExpbook/AutoCompleteServletSrtp'
    data = 'word=%s&index=%d&currentPage=%d&sql=stuSql&building=undefined&srtp_teacher_project_num=undefined&planyear=undefined' % (school_id, index, page)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    resp = requests.post(url, data=data.encode('utf8'), headers=headers)
    assert resp.status_code == 200
    return resp.text

