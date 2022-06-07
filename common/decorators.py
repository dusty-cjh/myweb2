from functools import wraps
from django.core.cache import cache
from .middlewares import get_logger


def cache_func_result(prefix='', timeout=600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = '{}.{}'.format(prefix, repr(args) + repr(kwargs))
            if ret := cache.get(key, None):
                return ret
            else:
                ret = func(*args, **kwargs)
                cache.set(key, ret, timeout)
                return ret
        return wrapper
    return decorator


def cache_coro_result(prefix='', timeout=600):
    def decorator(coro):
        @wraps(coro)
        async def wrapper(*args, **kwargs):
            key = '{}.{}'.format(prefix, repr(args) + repr(kwargs))
            if ret := await cache.aget(key, None):
                return ret
            else:
                ret = await coro(*args, **kwargs)
                await cache.aset(key, ret, timeout)
                return ret
        return wrapper
    return decorator


def async_csrf_exempt(func):
    async def wrapped_view(request, *args, **kwargs):
        resp = await func(request, *args, **kwargs)
        return resp

    wrapped_view.csrf_exempt = True
    return wraps(func)(wrapped_view)


def async_access_log(func_name=None):
    def decorator(func):
        @wraps(func)
        async def wrapped_view(request, *args, **kwargs):
            log = get_logger(request)
            if func_name:
                log = log.with_field('func', func_name)

            log.access('request={}', request.body)
            resp = await func(request, *args, **kwargs)
            log.access('response={}', resp.content)
            return resp

        return wrapped_view

    return decorator
