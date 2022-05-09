import asyncio as aio
import sys
from threading import Thread
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async as s2a

from django.http.request import HttpRequest
from common import utils
from .models import OneBotEvent, AsyncJobLock, AsyncJobConfig, AsyncJob
from . import settings as constants


async def process_async_job():
    statistic = {}
    success, failed = 0, 0
    for cfg in AsyncJobConfig.objects.all():
        # get async job lock
        if not await s2a(AsyncJobLock.lock)(cfg.job_name):
            continue

        # get async job list and process async job
        for job in await s2a(lambda x: list(AsyncJob.get_active_job_list_by_name(x)))(cfg.job_name):
            # execute job
            try:
                err = cfg.handler(job)
            except Exception as err:
                pass

            # update job params
            job_statistic = statistic.setdefault(job.name, {})
            if err:
                job.retries += 1
                job.result = repr(err)
                # store running statistic
                job_statistic['failed'] = job_statistic.setdefault('failed', 0) + 1
                failed += 1
            else:
                job.result = 'success'
                # store running statistic
                job_statistic['success'] = job_statistic.setdefault('success', 0) + 1
                success += 1
            now = utils.get_utils.get_datetime_now()
            job.mtime = now

            # check whether job is failed
            if job.retries == job.max_retry:
                job.status = AsyncJob.STATUS_FAIL

            # save updates
            job.save()

        # release async job lock
        await s2a(AsyncJobLock.unlock)(cfg.job_name)

    # print analysis
    if success + failed > 0:
        print('[async_job]total_success=%d, total_failed=%d' % (success, failed), file=sys.stderr)
        for k, v in statistic.items():
            print('[async_job][%s]success=%d, failed=%d' % (k, v['success'], v['failed']), file=sys.stderr)


async def run():
    while True:
        end_time = utils.get_datetime_now() + timedelta(seconds=5)

        # process async job
        await process_async_job()

        # process timeout event
        timeout_keys = []
        for key, msg_exchanger in MESSAGE_POOL.items():
            if msg_exchanger.has_timeout():
                msg_exchanger.process_timeout()
                timeout_keys.append(key)
        for key in timeout_keys:
            try:
                MESSAGE_POOL.pop(key)
            except KeyError:
                pass

        # have a rest
        cur_time = utils.get_datetime_now()
        if cur_time < end_time:
            t = end_time.timestamp() - cur_time.timestamp()
            await aio.sleep(t)


def main(l: aio.AbstractEventLoop):
    print('[mybot.event_loop] start', file=sys.stderr)
    try:
        l.run_until_complete(run())
    except Exception as e:
        print('[mybot.event_loop] event loop error: %s', repr(e), file=sys.stderr)
        raise e
    print('[mybot.event_loop] done', file=sys.stderr)


EVENT_LOOP = aio.new_event_loop()
EVENT_LOOP_THREAD = Thread(target=main, args=(EVENT_LOOP,), name='mybot.event_loop')
EVENT_LOOP_THREAD.start()
MESSAGE_POOL = {}


class MessageExchanger:
    msg_result: aio.Future
    timeout: datetime
    session_key: str
    on_timeout = None

    def __init__(self, session_key, timeout=300):
        self.msg_result = EVENT_LOOP.create_future()
        self.timeout = utils.get_datetime_now() + timedelta(seconds=timeout)
        self.session_key = session_key
        self.start_time = utils.get_datetime_now().timestamp()

    def has_timeout(self) -> bool:
        return utils.get_datetime_now() > self.timeout

    def process_message(self, request: HttpRequest, e):
        self.msg_result.set_result(e)

    def process_timeout(self):
        if self.on_timeout:
            return self.on_timeout()
        else:
            self.msg_result.set_exception(aio.TimeoutError('MessageExchanger timeout'))

    def __repr__(self):
        return f'{self.session_key}({self.timeout.timestamp() - utils.get_datetime_now().timestamp()})'


def get_msg_exchanger(session_key) -> MessageExchanger:
    return MESSAGE_POOL.get(session_key)


def pop_msg_exchanger(session_key) -> MessageExchanger:
    if session_key in MESSAGE_POOL:
        MESSAGE_POOL.pop(session_key)


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


# get_message - get message by user_id or group_id or both of them
async def get_message(user_id: int = None, group_id: int = None, timeout: int = 300) -> (OneBotEvent, str):
    session_key = get_session_key(user_id, group_id)
    exchanger = MessageExchanger(session_key, timeout)
    MESSAGE_POOL[session_key] = exchanger
    try:
        msg = await exchanger.msg_result
    except aio.TimeoutError as err:
        return None, err
    else:
        return msg, None


def process_message(request: HttpRequest, event: OneBotEvent):
    # check
    if event.post_type != constants.EVENT_POST_TYPE_MESSAGE:
        return

    # get session key
    session_key = ''
    if event.message_type == constants.EVENT_MESSAGE_TYPE_PRIVATE:
        session_key = get_session_key(user_id=event.user_id)
    elif event.message_type == constants.EVENT_MESSAGE_TYPE_GROUP:
        session_key = get_session_key(user_id=event.user_id, group_id=event.group_id)

    # process message if session key exists
    if msg_exchanger := get_msg_exchanger(session_key):
        if msg_exchanger.start_time <= event.time:
            ret = msg_exchanger.process_message(request, event)
            pop_msg_exchanger(session_key)
            if ret:
                return ret


def call(coro):
    task = EVENT_LOOP.create_task(coro)
    return task
