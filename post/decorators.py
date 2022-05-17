import asyncio as aio
from functools import wraps
from asgiref.sync import sync_to_async as s2a
from common.logger import Logger
from .models import AsyncFuncJob, MAX_RETRY, MAX_LIFETIME


_TRACE_ID = '_trace'


def _parse_coroutine_job_params(func):
    @wraps(func)
    async def wrapper(job: AsyncFuncJob, *args, **kwargs):
        data = job.parse_params()
        kwargs['job'] = job
        kwargs.update(data)
        result = await func(*args, **kwargs)
        return result

    return wrapper


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
    def __init__(self, func, max_retry=MAX_RETRY, max_lifetime=MAX_LIFETIME):
        self.func = func
        self.max_retry = max_retry
        self.max_lifetime = max_lifetime

    async def __call__(self, job: AsyncFuncJob):
        return await self.run_job(job)

    async def run_job(self, job: AsyncFuncJob):
        """ run async function job """
        # get var
        data = job.parse_params()
        result = job.parse_result() or {}
        args, kwargs = data.get('args', tuple()), data.get('kwargs', dict())
        log = get_async_job_logger(trace_id=result.get(_TRACE_ID))
        context = AsyncCoroutineFuncContext(job, log)

        # run job
        try:
            ret = await self.call(context, *args, **kwargs)
        except Exception as e:
            return {
                'error': repr(e),
                _TRACE_ID: log.get_trace_id()
            }

        # return result
        if not isinstance(ret, dict):
            ret = repr(ret)
        ret = {
            'data': ret,
            _TRACE_ID: log.get_trace_id()
        }
        return ret

    async def call(self, *args, **kwargs):
        """ call wrapped function """
        ret = await self.func(*args, **kwargs)
        return ret

    async def add_job(self, *args, max_retry=None, max_lifetime=None, **kwargs):
        max_retry = max_retry or self.max_retry
        max_lifetime = max_lifetime or self.max_lifetime

        params = {
            'args': args,
            'kwargs': kwargs,
        }
        return await s2a(AsyncFuncJob.create)(
            self.func,
            params,
            job_type=AsyncFuncJob.JOB_TYPE_IS_COROUTINE | AsyncFuncJob.JOB_TYPE_HAS_SUB_TASK,
            max_retry=max_retry,
            max_lifetime=max_lifetime,
        )


def async_coroutine(max_retry=MAX_RETRY, max_lifetime=MAX_LIFETIME):
    def decorator(func):
        return AsyncCoroutineFunc(func, max_retry=max_retry, max_lifetime=max_lifetime)
    return decorator


class AsyncFunc:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def add_job(self, params: dict, max_retry=3, max_lifetime=3000):
        return AsyncFuncJob.create(
            self.func,
            params,
            job_type=AsyncFuncJob.JOB_TYPE_IS_COROUTINE | AsyncFuncJob.JOB_TYPE_HAS_SUB_TASK,
            max_retry=max_retry,
            max_lifetime=max_lifetime,
        )


def async_function(func):
    return AsyncFunc(func)


def get_async_job_logger(trace_id=None):
    if trace_id:
        logger = Logger('async_job', trace_id)
    else:
        logger = Logger('async_job', auto_trace_id=True)

    return logger
