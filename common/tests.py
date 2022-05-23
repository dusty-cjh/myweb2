import asyncio as aio
import sys
import time

from post.models import AsyncFuncJob
from .utils import get_datetime_now


def tell_now(job: AsyncFuncJob):
    data = job.parse_params()
    msg = data.get('msg')

    # delay
    delay = int(data.get('delay', 0))
    if delay:
        time.sleep(delay)

    # fail
    fail = data.get('fail')
    if fail:
        raise RuntimeError('auto fail')

    print(msg, get_datetime_now(), file=sys.stderr)


async def atell_now(job: AsyncFuncJob):
    data = job.parse_params()
    msg = data.get('msg')

    # delay
    delay = int(data.get('delay', 0))
    if delay:
        await aio.sleep(delay)

    # fail
    fail = data.get('fail')
    if fail:
        raise RuntimeError('auto fail')

    print(msg, get_datetime_now(), file=sys.stderr)


def raise_exception(job: AsyncFuncJob):
    data = job.parse_params()
    raise TimeoutError(data.get('msg'))

