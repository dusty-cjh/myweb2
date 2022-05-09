import ujson
import aiohttp
from functools import wraps
from django.core.cache import cache
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

        def create_api(url):
            @wraps(get_response)
            async def wrapper(session: aiohttp.ClientSession = None, **kwargs):
                return await get_response('/' + url, session=session, **kwargs)
            return wrapper

        api_name_list = [k for k, v in attr_dict['__annotations__'].items() if v is get_response]
        for api_name in api_name_list:
            setattr(cls, api_name, create_api(api_name))


class OneBotApi(metaclass=OneBotApiMeta):
    send_private_msg: get_response
    send_group_msg: get_response
    send_msg: get_response
    delete_msg: get_response
    get_msg: get_response
    set_group_kick: get_response
    set_group_ban: get_response
    set_group_anonymous_ban: get_response
    get_group_info: get_response
    get_group_member_list: get_response
    get_group_member_info: get_response
    session = None

    def __init__(self, session: aiohttp.ClientSession = None, **kwargs):
        self.session = session or get_session()
        self.kwargs = kwargs

    @classmethod
    async def get_group_member_list_with_cache(cls, group_id) -> list[dict]:
        key = f'OneBotApi.get_group_member_list_with_cache.{group_id}'
        data = cache.get(key)
        if data:
            return data

        data = await cls.get_group_member_list(group_id=group_id)
        cache.set(key, data, 60)
        return data

    @classmethod
    async def get_group_admin_list_with_cache(cls, group_id) -> list[dict]:
        key = f'OneBotApi.get_group_admin_list_with_cache.{group_id}'
        data = cache.get(key)
        if data:
            return data

        data = await cls.get_group_member_list_with_cache(group_id=group_id)
        data = [x for x in data if x['role'] in ('admin', 'owner')]
        return data

    @classmethod
    async def get_group_member_info_with_cache(cls, group_id, user_id) -> dict:
        key = f'OneBotApi.get_group_member_info_with_cache.{group_id}.{user_id}'
        data = cache.get(key)
        if data:
            return data

        data = await cls.get_group_member_info(group_id=group_id, user_id=user_id)
        return data
