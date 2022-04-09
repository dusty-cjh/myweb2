import logging, re, yaml, json
from functools import wraps
from collections import namedtuple
from collections.abc import Mapping, MutableSequence
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.db.models import Model, QuerySet
from django.forms.models import model_to_dict

from common.constants import ErrCode, ErrMsg


class FrozenJson(dict):
    # base field
    errcode: int
    errmsg: str

    # wechat common field
    url: str
    media_id: str

    def __init__(self, arg=None, name='FrozenJson', ):
        if arg is None:
            arg = dict()
        for key, val in arg.items():
            arg[key] = self._wrap_element(val)

        super().__init__(arg)
        self.__name = name

    def __missing__(self, key):
        return None

    def __getattr__(self, item):
        return super().__getitem__(item)

    def __setattr__(self, key, value):
        return super().__setattr__(key, self._wrap_element(value))

    def __repr__(self):
        return '{}({})'.format(self.__name, ', '.join(['{}={}'.format(key, val) for key, val in self.items()]))

    @classmethod
    def _wrap_element(cls, obj):
        if obj.__class__ == dict:
            return cls(obj)
        elif isinstance(obj, MutableSequence):
            for i, val in enumerate(obj):
                obj[i] = cls._wrap_element(val)
            return obj
        else:
            return obj


def dict_to_namedtuple(name='dict_to_namedtuple'):
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            resp = {}
            try:
                resp = func(*args, **kwargs)
                resp['errcode'] = 0
                resp['errmsg'] = 'success'
            except Exception as e:
                resp['errcode'] = getattr(e, 'errcode', ErrCode.SUCCESS)
                resp['errmsg'] = repr(e)
            return FrozenJson(resp, name)
        return inner
    return decorator


def async_dict_to_namedtuple(name='dict_to_namedtuple'):
    def decorator(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            resp = {}
            try:
                resp = await func(*args, **kwargs)
                resp['errcode'] = 0
                resp['errmsg'] = 'success'
            except Exception as e:
                resp['errcode'] = getattr(e, 'errcode', ErrCode.SUCCESS)
                resp['errmsg'] = repr(e)
            return FrozenJson(resp, name)
        return inner
    return decorator


def error_recovery(func):
    @wraps(func)
    async def wrap(*args, **kwargs):
        try:
            resp = await func(*args, **kwargs)
        except OSError as e:
            return error_response(ErrCode.DHT_SOCK_CLOSED, repr(e))
        return resp
    return wrap


def _error_response(errmsg, status):
    return {
        'errcode': status,
        'errmsg': repr(errmsg),
    }, status & 0x3ff


def _response(data, status):
    # serialize django model
    if isinstance(data, Model):
        data = model_to_dict(data)

    # return data
    data.update({
        'errcode': status,
        'errmsg': 'success',
    })

    return data, status & 0x3ff


def json_error_response(errmsg, status=400):
    data, status = _error_response(errmsg, status)
    return JsonResponse(data, status=status)


def json_response(data, status=200):
    data, status = _response(data, status)
    return JsonResponse(data, status=status)


def yaml_error_response(errmsg, status=400):
    data, status = _error_response(errmsg, status)
    ret = yaml.dump(data)
    return HttpResponse(ret, content_type='text/yaml', status=status)


def yaml_response(data, status=200):
    data, status = _response(data, status)
    ret = yaml.dump(data)
    return HttpResponse(ret, content_type='text/yaml', status=status)


class Response(HttpResponse):
    content_type = 'application/json'

    def __init__(self, status, data=None, errmsg='success', content_type=None, *args, **kwargs):
        if data is None:
            data = dict()
        if content_type is None:
            content_type = self.content_type

        # update kwargs
        if status:
            kwargs['status'] = status & 0x3ff
        kwargs['content_type'] = content_type

        # prepare response data
        if isinstance(data, Model):
            data = model_to_dict(data)
        data.update({
            'errcode': status,
            'errmsg': errmsg,
        })

        # serialize response
        if content_type == 'text/yaml':
            content = yaml.dump(data)
        else:
            content = json.dumps(data)

        super().__init__(content=content, *args, **kwargs)


class JsonResp(Response):
    pass


class YamlResp(Response):
    content_type = 'text/yaml'


def _parse_data_from_markdown():
    regexp = re.compile(r'```yaml\s+(.*)```\s*$', flags=re.DOTALL | re.MULTILINE)

    def method(data: str):
        m = regexp.search(data)
        if m is None:
            return data, dict()
        meta = yaml.safe_load(m.groups()[0])
        return data[:m.start()], meta
    return method


parse_data_from_markdown = _parse_data_from_markdown()


def error_response(errcode, errmsg='', status=200):
    return {
        'errcode': errcode,
        'errmsg': ErrMsg.get(errcode, ErrMsg[ErrCode.UNKNOWN]) + ('' if not errmsg else f'|{errmsg}')
    }
