import logging
from functools import wraps
from collections import namedtuple
from collections.abc import Mapping, MutableSequence
from django.http import JsonResponse

log = logging.getLogger('info')


class FrozenJson(dict):
    def __init__(self, arg=None, name='FrozenJson', ):
        if arg is None:
            arg = dict()
        for key, val in arg.items():
            arg[key] = self._wrap_element(val)

        super().__init__(arg)
        self.name = name

    def __missing__(self, key):
        return None

    def __getattr__(self, item):
        return super().__getitem__(item)

    def __setattr__(self, key, value):
        return super().__setattr__(key, self._wrap_element(value))

    def __repr__(self):
        return '{}({})'.format(self.name, ', '.join(['{}={}'.format(key, val) for key, val in self.items()]))

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
                resp['errcode'] = getattr(e, 'errcode', -1)
                resp['errmsg'] = getattr(e, 'errmsg', 'NONAME ERROR')
                log.error('{}|{}| args={}, kwargs={}, resp={}'.format(func.__name__, name, args, kwargs, resp))
            return FrozenJson(resp, name)
        return inner
    return decorator


def json_error_response(errmsg, status=400):
    return JsonResponse({
        'errcode': status,
        'errmsg': errmsg,
    }, status=status)
