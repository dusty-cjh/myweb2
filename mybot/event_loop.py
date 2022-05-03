import asyncio as aio
import sys
from threading import Thread
from datetime import datetime, timedelta

from django.http.request import HttpRequest
from .models import OneBotEvent
from . import settings as constants


async def run():
    while True:
        await aio.sleep(5)


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
    on_timeout: None
    session_key: str

    def __init__(self, session_key, timeout=300):
        self.msg_result = EVENT_LOOP.create_future()
        self.timeout = datetime.now() + timedelta(timeout)
        self.session_key = session_key

    def has_timeout(self) -> bool:
        return datetime.now() > self.timeout

    def process_message(self, request: HttpRequest, e):
        self.msg_result.set_result(e)

    def process_timeout(self, request: HttpRequest, e):
        if self.on_timeout:
            return self.on_timeout(request, e)
        else:
            self.msg_result.set_exception(aio.TimeoutError('MessageExchanger timeout'))


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


def get_message(user_id: int = None, group_id: int = None, timeout: int = 300):
    session_key = get_session_key(user_id, group_id)
    exchanger = MessageExchanger(session_key, timeout)
    MESSAGE_POOL[session_key] = exchanger
    return exchanger.msg_result


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
    propagate = True
    if msg_exchanger := get_msg_exchanger(session_key):
        if msg_exchanger.has_timeout():
            propagate = msg_exchanger.process_timeout(request, event)
        else:
            propagate = msg_exchanger.process_message(request, event)
        pop_msg_exchanger(session_key)

    return {} if propagate else None


def call(coro):
    task = EVENT_LOOP.create_task(coro)
    return task


