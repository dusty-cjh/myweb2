from collections import namedtuple
from django.db import models
from django.http.request import HttpRequest

from common.middlewares import LoggingContextAdapter
from common.utils import chain
from . import settings as constants


class AsyncJob(models.Model):
    STATUS_INIT = 0
    STATUS_PENDING = 1
    STATUS_RUNNING = 2
    STATUS_PAUSE = 3
    STATUS_FAIL = 4
    STATUS_SUCCESS = 5
    STATUS = (
        (STATUS_INIT, 'initialized'),
        (STATUS_PENDING, 'pending'),
        (STATUS_RUNNING, 'running'),
        (STATUS_PAUSE, 'pause'),
        (STATUS_FAIL, 'fail'),
        (STATUS_SUCCESS, 'success'),
    )

    name = models.CharField(max_length=30)
    category = models.SmallIntegerField(default=-1)
    description = models.CharField(max_length=128, default='')
    params = models.TextField()

    max_retry = models.SmallIntegerField(default=1, verbose_name='max retry times')
    retries = models.SmallIntegerField(default=0, verbose_name='retry times count')
    retry_interval = models.PositiveSmallIntegerField(default=30, verbose_name='retry interval in seconds')

    status = models.SmallIntegerField(choices=STATUS, default=STATUS_INIT)
    result = models.TextField()
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='created timestamp')
    mtime = models.DateTimeField(verbose_name='modified timestamp')

    def __str__(self):
        return 'AsyncJob(id=%d, name=%s, params=%s)'.format(self.id, self.name, self.params)


class AsyncJobLock(models.Model):
    STATUS_UNLOCK = 0
    STATUS_LOCKED = 1
    STATUS = (
        (STATUS_UNLOCK, 'unlocked'),
        (STATUS_LOCKED, 'locked'),
    )

    job_name = models.CharField(max_length=30, verbose_name='async job name to lock')
    status = models.SmallIntegerField(choices=STATUS, default=STATUS_UNLOCK)
    handler_name = models.CharField(max_length=64, verbose_name='handler name')
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='created timestamp')
    mtime = models.DateTimeField(verbose_name='modified timestamp')
    exec_interval = models.PositiveSmallIntegerField(default=30, verbose_name='job queue execute interval in seconds')

    def __str__(self):
        return 'AsyncJobLock(id=%d, job_name=%s, status=%d)'.format(self.id, self.job_name, self.status)


class OneBotSender:
    user_id: int
    nickname: str
    sex: str
    age: int


class OneBotAnonymous:
    id: int
    name: str
    flag: str


class OneBotFile:
    id: str
    name: str
    size: int
    busid: int

    url: str


class OneBotEvent:
    time: int
    self_id: int
    post_type: str
    message_type: str
    sub_type: str
    temp_source: int
    message_id: int
    user_id: int
    message: str
    raw_message: str
    font: int
    sender: OneBotSender

    group_id: int
    anonymous: OneBotAnonymous

    notice_type: str
    file: OneBotFile

    operator_id: int

    # pin user
    sender_id: int
    target_id: int

    honor_type: str

    card_new: str
    card_old: str

    request_type: str
    comment: str


def create_event(event: dict) -> OneBotEvent:
    event_class = namedtuple(OneBotEvent.__name__, list(event.keys()))
    event = event_class(**event)
    return event


def get_event_name(event: OneBotEvent):
    name = event.post_type
    if event.post_type == constants.EVENT_POST_TYPE_MESSAGE:
        name = '{}.{}.{}'.format(name, event.message_type, event.sub_type)
    elif event.post_type == constants.EVENT_POST_TYPE_REQUEST:
        name = '{}.{}'.format(name, event.request_type)
    elif event.post_type == constants.EVENT_POST_TYPE_NOTICE:
        name = '{}.{}'.format(name, event.notice_type)
    if hasattr(event, 'sub_type'):
        name = '{}.{}'.format(name, event.sub_type)
    return name


class AbstractOneBotEventHandler:
    log: LoggingContextAdapter

    def __init__(self, request: HttpRequest, context=None, **kwargs):
        self.context = context or dict()
        self.request = request
        self.log = request.log

    async def dispatch(self, event: OneBotEvent, *args, **kwargs):
        event_name = get_event_name(event)
        for handler_name in chain(event_name.split('.'), sep='_', prefix='event'):
            if h := getattr(self, handler_name, None):
                return await h(event, *args, **kwargs)

    # ============ message event ===============

    async def event_message_private_friend(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_private_group(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_private_group_self(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_private_other(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_group_normal(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_group_anonymous(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_group_notice(self, event: OneBotEvent, *args, **kwargs):
        pass

    # ============= notice event ===============

    async def event_notice_group_upload(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_admin_set(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_admin_unset(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_decrease_leave(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_decrease_kick(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_decrease_kick_me(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_increase_approve(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_increase_invite(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_ban_ban(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_ban_lift_ban(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_friend_add(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_recall(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_friend_recall(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_notify_poke(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_notify_lucky_king(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_notify_honor(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_card(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_offline_file(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_client_status(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_essence_add(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_essence_delete(self, event: OneBotEvent, *args, **kwargs):
        pass

    # ============= request event ===============

    async def event_request_friend(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_request_group_add(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_request_group_invite(self, event: OneBotEvent, *args, **kwargs):
        pass

