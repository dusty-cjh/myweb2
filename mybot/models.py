import random

import ujson
from collections import namedtuple
from typing import Callable, List, Iterable
from datetime import datetime, timedelta
from django.db import models
from django.http.request import HttpRequest
from django.db.models import Q
from django.contrib.auth.models import User

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

    @classmethod
    def insert(
            cls, name: str, params: dict,
            description='',
            max_retry=3, retry_interval=30, status=0, category=0):
        now = datetime.now()
        obj = cls.objects.create(
            name=name, category=category, description=description, params=params,
            max_retry=max_retry, retries=0, retry_interval=retry_interval,
            status=status, ctime=now, mtime=now,
        )
        return obj

    @classmethod
    def get_job_list_by_name(cls, name: str, status=-1):
        qs = cls.objects.filter(name=name)
        if status != -1:
            qs = cls.objects.filter(status=status)
        return qs

    @classmethod
    def get_active_job_list_by_name(cls, name: str):
        qs = cls.objects.filter(name=name, status__lte=cls.STATUS_PAUSE)
        return qs

    def parse_params(self) -> dict:
        return ujson.loads(self.params)

    @classmethod
    def set_result_by_id(cls, id: int, result, status: int):
        if isinstance(result, dict):
            result = ujson.dumps(result)

        return cls.objects.filter(id=id).update(result=result, status=status, mtime=datetime.now())


class AsyncJobLock(models.Model):
    STATUS_UNLOCK = 0
    STATUS_LOCKED = 1
    STATUS = (
        (STATUS_UNLOCK, 'unlocked'),
        (STATUS_LOCKED, 'locked'),
    )

    job_name = models.CharField(max_length=30, primary_key=True, verbose_name='async job name to lock')
    status = models.SmallIntegerField(choices=STATUS, default=STATUS_UNLOCK)
    handler_name = models.CharField(max_length=64, verbose_name='handler name')
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='created timestamp')
    mtime = models.DateTimeField(verbose_name='modified timestamp', null=True)
    next_exec_time = models.DateTimeField(verbose_name='next timestamp to execute tasks', null=True)

    def __str__(self):
        return 'AsyncJobLock(job_name=%s, status=%d)'.format(self.job_name, self.status)

    @classmethod
    def lock(cls, job_name: str) -> bool:
        qs = cls.objects.filter(
            job_name=job_name,
            status=cls.STATUS_UNLOCK,
            next_exec_time__lte=datetime.now(),
        )
        count = qs.update(
            status=cls.STATUS_LOCKED,
            mtime=datetime.now(),
        )
        if count > 1:
            raise RuntimeError('AsyncJobLock.lock|job_name=%s|updated more than 1 row' % job_name)
        return bool(count)

    @classmethod
    def unlock(cls, job_name: str, interval=30) -> bool:
        qs = cls.objects.filter(
            job_name=job_name,
            status=cls.STATUS_LOCKED,
        )
        count = qs.update(
            status=cls.STATUS_UNLOCK,
            next_exec_time__lte=datetime.now() + timedelta(seconds=interval),
        )
        if count > 1:
            raise RuntimeError('AsyncJobLock.unlock|job_name=%s|updated more than 1 row' % job_name)
        return bool(count)

    # ----------- config

    JOB_LIST = []

    @classmethod
    def add_job_config(
            cls,
            job_name: str,
            category: int,
            handler: Callable,
            description='',
            retry_interval=30,
            max_retry=3,
            status=0,
    ):
        # global
        params = {k: v for k, v in locals().items()}
        params.pop('cls')

        # save job config
        cls.JOB_LIST.append(params)


class AsyncJobConfig:
    class objects:
        JOB_LIST = {}

        @classmethod
        def get_or_create(
                cls,
                job_name: str,
                handler: Callable,
                description='',
                retry_interval=30,
                max_retry=3,
                status=0,
                category=0,
        ):
            # create async job config
            params = {k: v for k, v in locals().items()}
            params.pop('cls')
            cfg = AsyncJobConfig()
            for k, v in params.items():
                setattr(cfg, k, v)
            cls.JOB_LIST[job_name] = cfg

            # get or create async_job_lock
            now = datetime.now()
            job_config, created = AsyncJobLock.objects.get_or_create(
                job_name=job_name,
                defaults=dict(status=AsyncJobLock.STATUS_UNLOCK, handler_name='')
            )
            print('get job_config', job_config)
            if created:
                job_config.ctime = now
                job_config.mtime = now
                job_config.next_exec_time = now + timedelta(seconds=retry_interval + random.random() * 10)
                job_config.save()

            return cfg

        @classmethod
        def get_job_config_by_name(cls, job_name: str):
            return cls.JOB_LIST.get(job_name, None)

        @classmethod
        def all(cls) -> list:
            return cls.JOB_LIST.values()

    job_name: str
    category: int
    handler: Callable
    description = ''
    retry_interval = 30
    max_retry = 3
    status = 0


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


class UserProfile(models.Model):
    # user = models.OneToOneField('auth.User', on_delete=models.CASCADE, verbose_name='user')
    name = models.CharField(max_length=20, verbose_name='name')
    qq_number = models.PositiveIntegerField(verbose_name='qqq number')
    college = models.CharField(max_length=20, verbose_name='college name', default='YSU')
    college_student_number = models.CharField(max_length=20, verbose_name='college student number')
    ctime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = 'UserProfile'
        ordering = ['-ctime', ]

    def __str__(self):
        return f'{self.name}({self.college_student_number})'

    @classmethod
    def get_by_student_number(cls, college_student_number: str, college='YSU'):
        try:
            ret = cls.objects.filter(
                Q(college_student_number=college_student_number) &
                Q(college=college)
            ).first()
        except cls.DoesNotExist:
            return None
        else:
            return ret

    @property
    def enrollment_year(self):
        if self.college_student_number.startswith('20'):
            return int(self.college_student_number[:4])
        else:
            return int(f'20{self.college_student_number[:2]}')


# @receiver(post_save, sender=User)
# def profile_create(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)
