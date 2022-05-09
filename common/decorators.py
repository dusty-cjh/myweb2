from functools import wraps
from django.core.cache import cache
from .middlewares import get_logger


def cache_func_result(timeout=600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = 'f.r.{}'.format(repr(args) + repr(kwargs))
            if ret := cache.get(key, None):
                return ret
            else:
                ret = func(*args, **kwargs)
                cache.set(key, ret)
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
