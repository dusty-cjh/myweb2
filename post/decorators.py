import asyncio as aio
import inspect
import json
import traceback
import typing
import random
from functools import wraps
from datetime import timedelta
from asgiref.sync import sync_to_async as s2a
from common.logger import Logger
from common import utils
from .models import AsyncFuncJob, MAX_RETRY, MAX_LIFETIME


_TRACE_ID = 'trace'


def _parse_coroutine_job_params(func):
    @wraps(func)
    async def wrapper(job: AsyncFuncJob, *args, **kwargs):
        data = job.parse_params()
        kwargs['job'] = job
        kwargs.update(data)
        result = await func(*args, **kwargs)
        return result

    return wrapper


class AsyncJobException(Exception):
    def __init__(self, data: dict):
        self.data = data

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '|'.join([f'{k}={v}' for k, v in self.data.items()])


class AsyncCoroutineFuncContext:
    def __init__(self, job: AsyncFuncJob, log: Logger):
        self.job = job
        self.log = log

    async def update_kwargs(self, **update_fields):
        job = self.job
        data = job.parse_params()
        data.setdefault('kwargs', {}).update(update_fields)
        job.set_params(data)
        return await s2a(job.safe_update)(params=job.params)


class AsyncCoroutineFunc:
    def __init__(self, func: typing.Callable, max_retry=MAX_RETRY, max_lifetime=MAX_LIFETIME):
        self.func = func
        self.max_retry = max_retry
        self.max_lifetime = max_lifetime

        # register async job to current module
        func_module = inspect.getmodule(func)
        job_func_name = '#AsyncCoroutineFunc-%s' % func.__name__
        setattr(func_module, job_func_name, self.run_job)
        self.job_func_import_name = f'{func_module.__name__}.{job_func_name}'

    async def __call__(self, *args, **kwargs):
        return await self.call(*args, **kwargs)

    async def run_job(self, job: AsyncFuncJob, raise_exception=True, with_trace_id=False):
        """ run async function job """
        # get var
        data = job.parse_params()
        result = job.parse_result() or {}
        args, kwargs = data.get('args', tuple()), data.get('kwargs', dict())
        log = get_async_job_logger(trace_id=result.get(_TRACE_ID) or f'async_job.{job.id}.{job.retries}')
        context = AsyncCoroutineFuncContext(job, log)

        # run job
        try:
            ret = await self.call(context, *args, **kwargs)
        except Exception as e:
            ret = {
                'exception': repr(e),
                'stack': traceback.format_exc(),
                _TRACE_ID: log.get_trace_id()
            }
            if raise_exception:
                raise AsyncJobException(ret)
            else:
                return ret

        # with trace id
        if with_trace_id:
            if isinstance(ret, str):
                pass
            elif not isinstance(ret, dict):
                ret = repr(ret)
            ret = {
                'ret': ret,
                _TRACE_ID: log.get_trace_id()
            }
        return ret

    async def call(self, *args, **kwargs):
        """ call wrapped function """
        ret = await self.func(*args, **kwargs)
        return ret

    def get_job_creating_params(self, *args, max_retry=None, max_lifetime=None, **kwargs):
        now = utils.get_datetime_now()
        max_retry = max_retry or self.max_retry
        max_lifetime = max_lifetime or self.max_lifetime

        params = {
            'args': args,
            'kwargs': kwargs,
        }
        ret = dict(
            func_name=self.job_func_import_name,
            params=json.dumps(params),
            job_type=AsyncFuncJob.JOB_TYPE_IS_COROUTINE | AsyncFuncJob.JOB_TYPE_HAS_SUB_TASK,
            max_retry=max_retry,
            max_lifetime=max_lifetime,
            expire_time=now + timedelta(seconds=max_lifetime),
            mtime=now,
        )
        return ret

    async def add_job(self, *args, max_retry=None, max_lifetime=None, **kwargs):
        params = self.get_job_creating_params(*args, max_retry=max_retry, max_lifetime=max_lifetime, **kwargs)
        return await s2a(AsyncFuncJob.objects.create)(**params)


def async_coroutine(max_retry=MAX_RETRY, max_lifetime=MAX_LIFETIME):
    def decorator(func):
        return AsyncCoroutineFunc(func, max_retry=max_retry, max_lifetime=max_lifetime)
    return decorator


class AsyncFuncContext:
    def __init__(self, job: AsyncFuncJob, log: Logger):
        self.job = job
        self.log = log

    def update_kwargs(self, **update_fields):
        job = self.job
        data = job.parse_params()
        data.setdefault('kwargs', {}).update(update_fields)
        job.set_params(data)
        return job.safe_update(params=job.params)


class AsyncFunc(AsyncCoroutineFunc):
    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def call(self, *args, **kwargs):
        """ call wrapped function """
        ret = self.func(*args, **kwargs)
        return ret

    def add_job(self, *args, max_retry=None, max_lifetime=None, **kwargs):
        params = self.get_job_creating_params(*args, max_retry=max_retry, max_lifetime=max_lifetime, **kwargs)
        return AsyncFuncJob.objects.create(**params)

    def run_job(self, job: AsyncFuncJob, raise_exception=True, with_trace_id=False):
        """ run async function job """
        # get var
        data = job.parse_params()
        result = job.parse_result() or {}
        args, kwargs = data.get('args', tuple()), data.get('kwargs', dict())
        log = get_async_job_logger(trace_id=result.get(_TRACE_ID))
        context = AsyncFuncContext(job, log)

        # run job
        try:
            ret = self.call(context, *args, **kwargs)
        except Exception as e:
            ret = {
                'exception': repr(e),
                'stack': traceback.format_exc(),
                _TRACE_ID: log.get_trace_id()
            }
            if raise_exception:
                raise AsyncJobException(ret)
            else:
                return ret

        # with trace id
        if with_trace_id:
            if isinstance(ret, str):
                pass
            elif not isinstance(ret, dict):
                ret = repr(ret)
            ret = {
                'ret': ret,
                _TRACE_ID: log.get_trace_id()
            }
        return ret


def async_function(max_retry=MAX_RETRY, max_lifetime=MAX_LIFETIME):
    def decorator(func):
        return AsyncFunc(func, max_retry=max_retry, max_lifetime=max_lifetime)
    return decorator


def get_async_job_logger(trace_id=None):
    if trace_id:
        logger = Logger('async_job', trace_id)
    else:
        logger = Logger('async_job', auto_trace_id=True)

    return logger
