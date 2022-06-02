import re
import time
import ujson as json
import asyncio as aio
import aiohttp
import typing
import requests
from django.core.cache import cache
from django.utils.html import escape
from common.utils import ErrCode
from . import helper
from .settings import ONE_BOT


class AsyncOneBotApi:

    class Options:
        max_retry: int = ONE_BOT.get('max_retry', 1)
        fixed_values: dict = None
        timeout: float = ONE_BOT['timeout']
        host: str = ONE_BOT['host']
        access_token: str = ONE_BOT['access_token']
        cache_timeout: float = None

        def copy(self):
            options = self.__class__()
            options.__dict__ = self.__dict__.copy()
            return options

    def __init__(self, options=None):
        if options is None:
            options = self.__class__.Options()
        self.options = options

    async def _get_response(self, url: str, **kwargs):
        # global
        ret, err = None, None
        cache_key = None

        # get from cache
        if self.options.cache_timeout is not None:
            data = json.dumps(kwargs, sort_keys=True)
            cache_key = hash(url + data)
            data = cache.get(cache_key)
            if data:
                data = json.loads(data)
                return data, ErrCode.SUCCESS

        # get url
        if not url.startswith('http'):
            url = self.options.host + url

        # get timeout
        timeout = aiohttp.ClientTimeout(total=self.options.timeout)

        # get sign
        headers = {
            'Authorization': 'Bearer %s' % self.options.access_token,
        }

        # get session
        session = aiohttp.ClientSession(
            json_serialize=json.dumps,
            timeout=timeout,
            headers=headers,
        )

        # get fixed value
        if self.options.fixed_values:
            params = self.options.fixed_values.copy()
            params.update(kwargs)
        else:
            params = kwargs

        # get response
        async with session:
            for i in range(self.options.max_retry):
                try:
                    async with session.post(url, json=params) as resp:
                        if errmsg := helper.get_errmsg_from_status(resp.status):
                            ret, err = 'response status=%d, errmsg=%s' % (resp.status, errmsg), ErrCode.CALL_3P_ERROR
                        else:
                            data = await resp.json(loads=json.loads)
                            if data['retcode'] != 0:
                                ret, err = data, helper.map_error(data['retcode'])
                            else:
                                ret, err = data['data'], ErrCode.SUCCESS
                except aiohttp.ClientConnectorError as e:
                    ret, err = e, ErrCode.CLIENT_CONNECTION_ERROR

                # check retry
                if not err:
                    break
                else:
                    await aio.sleep(0.2 * (i+1))

        # save to cache if necessary
        if cache_key is not None and not err:
            data = json.dumps(ret)
            cache.set(cache_key, data, self.options.cache_timeout)

        return ret, err

    def __getattr__(self, url: str):
        async def inner(**kwargs):
            resp, err = await self._get_response(url, **kwargs)
            return resp, err

        return inner

    def with_timeout(self, timeout):
        opts = self.options.copy()
        opts.timeout = timeout
        return self.__class__(opts)

    def with_fields(self, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        opts = self.options.copy()
        if opts.fixed_values:
            opts.fixed_values.update(kwargs)
        else:
            opts.fixed_values = kwargs
        return self.__class__(opts)

    def with_max_retry(self, max_retry: int):
        assert max_retry > 0
        opts = self.options.copy()
        opts.max_retry = max_retry
        return self.__class__(opts)

    def with_cache(self, timeout: float):
        opts = self.options.copy()
        opts.cache_timeout = timeout
        return self.__class__(opts)

    async def send_private_msg(self, message: str = None, user_id: int = None, group_id: int = None, auto_escape=False):
        params = {k: v for k, v in locals().items() if v not in (None, self)}
        return await self._get_response('send_private_msg', **params)

    async def send_group_msg(self, message: str, group_id: int = None, auto_escape=False):
        params = {k: v for k, v in locals().items() if v not in (None, self)}
        return await self._get_response('send_group_msg', **params)

    async def send_msg(self, **kwargs):
        return await self._get_response('send_msg', **kwargs)

    async def delete_msg(self, message_id):
        return await self._get_response('delete_msg', message_id=message_id)

    async def get_msg(self, **kwargs):
        return await self._get_response('get_msg', **kwargs)

    async def set_group_kick(self, group_id: int, user_id: int, reject_add_request=False):
        params = {k: v for k, v in locals().items() if v not in (None, self)}
        return await self._get_response('set_group_kick', **params)

    async def set_group_ban(self, **kwargs):
        return await self._get_response('set_group_ban', **kwargs)

    async def set_group_anonymous_ban(self, **kwargs):
        return await self._get_response('set_group_anonymous_ban', **kwargs)

    async def get_group_info(self, group_id: int, no_cache=False):
        return await self._get_response('get_group_info', group_id=group_id, no_cache=no_cache)

    async def get_group_list(self):
        return await self._get_response('get_group_list')


class OneBotApi:
    # api hint
    send_group_msg: typing.Callable
    send_msg: typing.Callable
    delete_msg: typing.Callable
    get_msg: typing.Callable
    set_group_kick: typing.Callable
    set_group_ban: typing.Callable
    set_group_anonymous_ban: typing.Callable
    get_group_info: typing.Callable
    get_group_list: typing.Callable

    class Options:
        max_retry: int = ONE_BOT.get('max_retry')
        fixed_values: dict = None
        timeout: float = ONE_BOT['timeout']
        host: str = ONE_BOT['host']
        access_token: str = ONE_BOT['access_token']
        cache_timeout: float = None

        def copy(self):
            options = self.__class__()
            options.__dict__ = self.__dict__.copy()
            return options

    def __init__(self, options=None):
        if options is None:
            options = self.__class__.Options()
        self.options = options

    def _get_response(self, url: str, **kwargs):
        # global
        ret, err = None, None
        cache_key = None

        # get from cache
        if self.options.cache_timeout is not None:
            data = json.dumps(kwargs, sort_keys=True)
            cache_key = hash(url + data)
            data = cache.get(cache_key)
            if data:
                data = json.loads(data)
                return data, ErrCode.SUCCESS

        # get url
        if not url.startswith('http'):
            url = self.options.host + url

        # get sign
        headers = {
            'Authorization': 'Bearer %s' % self.options.access_token,
        }

        # get fixed value
        if self.options.fixed_values:
            params = self.options.fixed_values.copy()
            params.update(kwargs)
        else:
            params = kwargs

        # get response
        for i in range(self.options.max_retry):
            resp = requests.post(url, json=params, headers=headers, timeout=self.options.timeout)
            if errmsg := helper.get_errmsg_from_status(resp.status_code):
                ret, err = 'response status=%d, errmsg=%s' % (resp.status_code, errmsg), ErrCode.CALL_3P_ERROR
            else:
                data = resp.json()
                if data['retcode'] != 0:
                    ret, err = data, helper.map_error(data['retcode'])
                else:
                    ret, err = data['data'], ErrCode.SUCCESS

            # check retry
            if not err:
                break
            else:
                time.sleep(0.2 * (i+1))

        # save to cache if necessary
        if cache_key is not None and not err:
            data = json.dumps(ret)
            cache.set(cache_key, data, self.options.cache_timeout)

        return ret, err

    def __getattr__(self, url: str):
        async def inner(**kwargs):
            resp, err = self._get_response(url, **kwargs)
            return resp, err

        return inner

    def with_timeout(self, timeout):
        opts = self.options.copy()
        opts.timeout = timeout
        return self.__class__(opts)

    def with_fields(self, **kwargs):
        opts = self.options.copy()
        if opts.fixed_values:
            opts.fixed_values.update(kwargs)
        else:
            opts.fixed_values = kwargs
        return self.__class__(opts)

    def with_max_retry(self, max_retry: int):
        opts = self.options.copy()
        opts.max_retry = max_retry
        return self.__class__(opts)

    def with_cache(self, timeout: float):
        opts = self.options.copy()
        opts.cache_timeout = timeout
        return self.__class__(opts)

    def send_private_msg(self, user_id: int, message: str, group_id: int = None, auto_escape=False):
        params = {k: v for k, v in locals().items() if v not in (None, self)}
        return self._get_response('send_group_msg', **params)

    def send_group_msg(self, **kwargs):
        return self._get_response('send_group_msg', **kwargs)

    def send_msg(self, **kwargs):
        return self._get_response('send_msg', **kwargs)

    def delete_msg(self, message_id):
        return self._get_response('delete_msg', message_id=message_id)

    def get_msg(self, **kwargs):
        return self._get_response('get_msg', **kwargs)

    def set_group_kick(self, **kwargs):
        return self._get_response('set_group_kick', **kwargs)

    def set_group_ban(self, **kwargs):
        return self._get_response('set_group_ban', **kwargs)

    def set_group_anonymous_ban(self, **kwargs):
        return self._get_response('set_group_anonymous_ban', **kwargs)

    def get_group_info(self, group_id: int, no_cache=False):
        return self._get_response('get_group_info', group_id=group_id, no_cache=no_cache)

    def get_group_list(self):
        return self._get_response('get_group_list')


class CQCodeConfig:
    type: str
    data: dict

    def __init__(self, type: str, **data):
        self.type = type
        self.data = data

    def render(self):
        body = ','.join(['{k}={v}'.format(k=k, v=v) for k, v in self.data.items()])
        return '[CQ:{},{}]'.format(self.type, body)

    def __str__(self):
        return self.render()


class CQCode:
    reg_cq = re.compile(r'\[CQ:(\w+),(.*?)\]')
    @classmethod
    def face(cls, id):
        return cls._render('face', id=id)

    @classmethod
    def record(cls, file):
        return cls._render('record', file=file)

    @classmethod
    def at(cls, qq, name=None):
        data = {
            'qq': qq,
        }
        if name:
            data['name'] = name
        return cls._render('at', **data)
    at.pattern = re.compile(r'\[CQ:at,(.*?)\]')

    @classmethod
    def at_all(cls):
        return cls.at('all')

    @classmethod
    def poke(cls, qq):
        return cls._render('poke', qq=qq)

    @staticmethod
    def _render(type: str, **data):
        body = ','.join(['{k}={v}'.format(k=k, v=v) for k, v in data.items()])
        return '[CQ:{},{}]'.format(type, body)

    @classmethod
    def parse_cq_code_list(cls, message: str):
        obj_list = []
        matches = cls.reg_cq.findall(message)
        for type, data in matches:
            data = [x.split('=') for x in data.split(',')]
            data = {x[0]: x[1] for x in data}
            obj = CQCodeConfig(type, **data)
            obj_list.append(obj)
        return obj_list
