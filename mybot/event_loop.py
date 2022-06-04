import asyncio as aio
import sys
from threading import Thread
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async as s2a

from django.http.request import HttpRequest
from django.conf import settings
from bridge.onebot import OneBotEvent
from bridge.onebot import constants
from common import utils, constants as common_constants
from post.models import AsyncFuncJob, MAX_RETRY, MAX_LIFETIME
from post.decorators import get_async_job_logger


async def run():
    def delete_done_event(pool: dict):
        done_keys = []
        for key, val in pool.items():
            if isinstance(val, aio.Future):
                if val.done() or val.cancelled():
                    done_keys.append(key)
            elif isinstance(val, dict):
                delete_done_event(val)
            else:
                raise ValueError('event_loop.delete_done_event: unexpected value type: %s' % type(val))

        for key in done_keys:
            pool.pop(key)

    while True:
        end_time = utils.get_datetime_now() + timedelta(seconds=5)
        loop = get_event_loop()

        # process async job
        job_list = await s2a(lambda: list(AsyncFuncJob.get_callable_list()))()
        for job in job_list:
            if job.is_coroutine:
                try:
                    func = job.get_coroutine()
                except ImportError as e:
                    await s2a(job.set_error)(dict(exception=repr(e)))
                else:
                    loop.create_task(func(job, with_trace_id=True))
            else:
                try:
                    func = job.get_function()
                except ImportError as e:
                    await s2a(job.set_error)(dict(exception=repr(e)))
                else:
                    loop.run_in_executor(None, func, job)

        # process timeout event
        delete_done_event(MESSAGE_POOL)

        # have a rest
        cur_time = utils.get_datetime_now()
        if cur_time < end_time:
            t = end_time.timestamp() - cur_time.timestamp()
            await aio.sleep(t)

        if settings.DEBUG:
            print('[event_loop running] asyncio.loop.event_count=%d, handled async func job %d, message pool size: %d' %
                  (len(aio.all_tasks(loop)), len(job_list), len(MESSAGE_POOL)))


def main(l: aio.AbstractEventLoop):
    if settings.DEBUG:
        print('[mybot.event_loop] start', file=sys.stderr)
    else:
        log = get_async_job_logger('event_loop.main')
        log.info('[mybot.event_loop] start')
    try:
        l.run_until_complete(run())
    except KeyboardInterrupt:
        if settings.DEBUG:
            print('[mybot.event_loop] event loop quit: KeyboardInterrupt')
        else:
            log.warning('[mybot.event_loop] event loop quit: KeyboardInterrupt')
    except RuntimeError as e:
        if settings.DEBUG:
            raise e
        if repr(e) not in common_constants.PYTHON_INTERPRETER_SHUTDOWN:
            if settings.DEBUG:
                print('[mybot.event_loop] event loop have to restart, because runtime error: %s' % repr(e), file=sys.stderr)
            else:
                log.error('[mybot.event_loop] event loop have to restart, because runtime error: %s' % repr(e))
            main(l)
    except Exception as e:
        if settings.DEBUG:
            raise e
        else:
            log.error('[mybot.event_loop] event loop have to restart, because exception: %s' % repr(e))
        main(l)
    if settings.DEBUG:
        print('[mybot.event_loop] done', file=sys.stderr)
    else:
        log.warning('[mybot.event_loop] done')


_EVENT_LOOP = None
_EVENT_LOOP_THREAD = None
MESSAGE_POOL = {
    'message': {
        'private': {},
        'group': {},
    },
}


def get_event_loop() -> aio.AbstractEventLoop:
    global _EVENT_LOOP, _EVENT_LOOP_THREAD

    if not _EVENT_LOOP:
        _EVENT_LOOP = aio.new_event_loop()

    if _EVENT_LOOP.is_closed() or not _EVENT_LOOP_THREAD or not _EVENT_LOOP_THREAD.is_alive():
        if _EVENT_LOOP_THREAD:
            try:
                _EVENT_LOOP_THREAD.join(1)
            except Exception:
                pass

        if _EVENT_LOOP.is_running():
            _EVENT_LOOP.stop()

        _EVENT_LOOP_THREAD = Thread(target=main, args=(_EVENT_LOOP,), name='mybot.event_loop', daemon=True)
        _EVENT_LOOP_THREAD.start()

    return _EVENT_LOOP


def get_session_key(user_id: int = None, group_id: int = None):
    session_key = ''
    if user_id:
        session_key += f'u{user_id}'
    if group_id:
        session_key += f'g{group_id}'

    # validate
    if not session_key:
        raise AssertionError('user_id or group_id must be provided')

    return session_key


def _get_session_key_of_private_message(user_id: int):
    return 'message.private.{}'.format(user_id)


def process_message(request: HttpRequest, event: OneBotEvent):
    # check
    if event.post_type != constants.EVENT_POST_TYPE_MESSAGE:
        return

    # process message if session key exists
    if pool := MESSAGE_POOL.get(event.post_type):
        if pool := pool.get(event.message_type):
            # user message
            user_id = getattr(event, 'user_id', None)
            if user_id in pool:
                fut = pool.pop(user_id)
                if not (fut.done() or fut.cancelled()):
                    fut.set_result(event)
                    return {}


def call(coro):
    loop = get_event_loop()
    task = loop.create_task(coro)
    return task


ASYNC_TASK_LIST = []


async def create_async_task(func, params, max_retry=MAX_RETRY, max_lifetime=MAX_LIFETIME):
    job = s2a(AsyncFuncJob.create)(
        func, params,
        job_type=AsyncFuncJob.JOB_TYPE_IS_COROUTINE | AsyncFuncJob.JOB_TYPE_HAS_SUB_TASK,
        max_lifetime=max_lifetime,
        max_retry=max_retry,
    )
    return job
