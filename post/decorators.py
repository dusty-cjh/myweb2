import asyncio as aio
from functools import wraps
from asgiref.sync import sync_to_async as s2a
from common.logger import Logger
from .models import AsyncFuncJob


def _parse_coroutine_job_params(func):
    @wraps(func)
    async def wrapper(job: AsyncFuncJob, *args, **kwargs):
        data = job.parse_params()
        kwargs['job'] = job
        kwargs.update(data)
        result = await func(*args, **kwargs)
        return result

    return wrapper


class AsyncCoroutineFunc:
    def __init__(self, func):
        self.func = _parse_coroutine_job_params(func)

    async def __call__(self, *args, **kwargs):
        return await self.func(*args, **kwargs)

    async def add_job(self, *args, max_retry=3, max_lifetime=3000, **kwargs):
        params = {
            'args': args,
            'kwargs': kwargs,
        }
        return await s2a(AsyncFuncJob.create)(
            self.func,
            params,
            job_type=AsyncFuncJob.IS_COROUTINE | AsyncFuncJob.HAS_SUB_TASK,
            max_retry=max_retry,
            max_lifetime=max_lifetime,
        )


def async_coroutine(func):
    return AsyncCoroutineFunc(func)


class AsyncFunc:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def add_job(self, params: dict, max_retry=3, max_lifetime=3000):
        return AsyncFuncJob.create(
            self.func,
            params,
            job_type=AsyncFuncJob.IS_COROUTINE | AsyncFuncJob.HAS_SUB_TASK,
            max_retry=max_retry,
            max_lifetime=max_lifetime,
        )


def async_function(func):
    return AsyncFunc(func)


def get_async_job_logger():
    logger = Logger('async_job', auto_trace_id=True)
    return logger
