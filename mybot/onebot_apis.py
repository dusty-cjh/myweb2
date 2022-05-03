import ujson
import aiohttp

from .settings import ONE_BOT, get_errmsg_from_status


def get_session():
    timeout = aiohttp.ClientTimeout(total=ONE_BOT['timeout'])
    headers = {
        'Authorization': 'Bearer %s' % ONE_BOT['access_token'],
    }
    session = aiohttp.ClientSession(
        json_serialize=ujson.dumps,
        timeout=timeout,
        headers=headers,
    )
    return session


async def get_response(url: str, session: aiohttp.ClientSession = None, **kwargs):
    # get params
    if session is None:
        session = get_session()

    # get url
    if not url.startswith('http'):
        url = ONE_BOT['host'] + url

    # get response
    async with session:
        async with session.post(url, json=kwargs) as resp:
            if errmsg := get_errmsg_from_status(resp.status):
                raise AssertionError('response status=%d, errmsg=%s' % (resp.status, errmsg))
            data = await resp.json(loads=ujson.loads)
            return data


class OneBotApiMeta(type):
    def __init__(cls, name, bases, attr_dict):
        super().__init__(name, bases, attr_dict)

        api_name_list = [k for k, v in attr_dict['__annotations__'].items() if v is get_response]
        for api_name in api_name_list:
            setattr(
                cls, api_name,
                lambda session=None, **kwargs: get_response('/' + api_name, session=session, **kwargs),
            )


class OneBotApi(metaclass=OneBotApiMeta):
    send_private_msg: get_response
    send_group_msg: get_response
    send_msg: get_response
    delete_msg: get_response
    get_msg: get_response
    set_group_kick: get_response
    set_group_ban: get_response
    set_group_anonymous_ban: get_response

