import datetime
from typing import Iterable
from common.constants import ErrCode, ErrMsg
from django.conf import settings


def read_attr_from_dict(instance: object, data: dict):
    setattr(instance, '_data', data)
    for key, val in data.items():
        if key in instance.__class__.__dict__ and 'a' < key[0] < 'z':
            setattr(instance, key, val)


def error_response(errcode, errmsg='', status=200):
    return {
        'errcode': errcode,
        'errmsg': ErrMsg.get(errcode, ErrMsg[ErrCode.UNKNOWN]) + ('' if not errmsg else f'|{errmsg}')
    }


def chain(ar: list, sep='', prefix=None):
    if prefix:
        yield prefix
        ret = prefix
    else:
        ret = ar[0]
        yield ret
        ar = ar[1:]

    for x in ar:
        ret = ret + sep + x
        yield ret


def get_datetime_now():
    ret = datetime.datetime.now(tz=settings.PY_TIME_ZONE)
    return ret


def update_json_obj(old: dict, latest: dict) -> dict:
    for key, old_val in old.items():
        latest_val = latest.get(key)
        if latest_val and old_val != latest_val:
            old[key] = latest[key]

    return old


def new_counter(start=0, step=1, to_string=False):
    def counter():
        nonlocal start

        while True:
            ret = str(start) if to_string else start
            yield ret
            start += step
    return counter
