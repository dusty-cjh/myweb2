import json
import random
import ujson
from collections import namedtuple
from typing import Callable, List, Iterable
from datetime import datetime, timedelta
from django.db import models
from django.http.request import HttpRequest
from django.db.models import Q, F, Func, Value
from django.contrib.auth.models import User
from django.core.cache import cache

from common.middlewares import LoggingContextAdapter
from common.utils import serializer
from common import utils
from mybot.onebot.serializers import OneBotEvent
from . import settings as constants

CLASS_NAME_PLUGIN_CONFIG = 'PluginConfig'


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
        for handler_name in utils.chain(event_name.split('.'), sep='_', prefix='event'):
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

    async def meta_event(self, event: OneBotEvent, *args, **kwargs):
        pass


# class SyncPluginConfigWithDB(serializer.SerializerMeta):
#     def __init__(cls, name, bases, attr_dict):
#         super().__init__(name, bases, attr_dict)
#         if name == CLASS_NAME_PLUGIN_CONFIG and AbstractOneBotPluginConfig in bases:
#             # global var
#             plugin_name = cls.name
#             plugin_default_configs = {}
#             for cfg_name in filter(lambda x: not x.startswith('_'), dir(cls)):
#                 plugin_default_configs[cfg_name] = getattr(cls, cfg_name)
#             plugin_default_configs.pop('name')
#             plugin_default_configs.pop('verbose_name')
#             plugin_default_configs.pop('short_description')
#
#             # sync config with DB
#             try:
#                 plugin_db_configs = PluginConfigs.objects.get(name=plugin_name)
#             except PluginConfigs.DoesNotExist:
#                 PluginConfigs.objects.create(
#                     name=plugin_name,
#                     verbose_name=cls.verbose_name,
#                     short_description=cls.short_description,
#                     configs=json.dumps(plugin_default_configs),
#                 )
#                 return
#             # else:
#             #     plugin_db_configs


class AbstractOneBotPluginConfig(serializer.Serializer):
    name = serializer.CharField(default='')
    verbose_name = serializer.CharField(default='')
    short_description = serializer.CharField(default='')
    readonly_fields = 'name verbose_name'.split()

    @classmethod
    def _get_module_name(cls):
        return cls.__module__.split('.')[-1]

    @classmethod
    def _serialize_default_config(cls):
        plugin_default_config = {}
        for field_name in cls._fields:
            field = getattr(cls, field_name)
            plugin_default_config[field_name] = field.default_value
        if not plugin_default_config['name']:
            plugin_default_config['name'] = cls._get_module_name()
        if not plugin_default_config['verbose_name']:
            plugin_default_config['verbose_name'] = plugin_default_config['name']
        return plugin_default_config

    @classmethod
    def get_default(cls):
        plugin_default_config = cls._serialize_default_config()
        return cls(**plugin_default_config)

    @classmethod
    def get_latest(cls):
        plugin_default_config = cls._serialize_default_config()
        try:
            obj = PluginConfigs.objects.get(name=cls._get_module_name())
        except PluginConfigs.DoesNotExist:
            # write default config to DB if it not exists
            kwargs = {}
            for field_name in cls.readonly_fields:
                kwargs[field_name] = plugin_default_config.pop(field_name)
            kwargs['configs'] = json.dumps(plugin_default_config)
            PluginConfigs.objects.create(**kwargs)
            return cls.get_default()
        else:
            # read and then flush in DB plugin config
            plugin_db_config = json.loads(obj.configs)
            utils.update_json_obj(plugin_default_config, plugin_db_config)
            return cls(**plugin_default_config)

    @classmethod
    def from_db_config(cls, obj):
        plugin_configs = utils.update_json_obj(cls._serialize_default_config(), json.loads(obj.configs))
        return cls(**plugin_configs)

    @classmethod
    def json_form_fields(cls):
        return cls._fields ^ set(cls.readonly_fields)


class OneBotCmdMixin:
    async def event_message_private_friend(self, event, *args, **kwargs):
        return await self.dispatch_cmd(event, *args, **kwargs)

    async def event_message_private_group(self, event: OneBotEvent, *args, **kwargs):
        return await self.dispatch_cmd(event, *args, **kwargs)

    async def event_message_group_normal(self, event: OneBotEvent, *args, **kwargs):
        return await self.dispatch_cmd(event, *args, **kwargs)

    async def dispatch_cmd(self, event: OneBotEvent, *args, **kwargs):
        cmd_args = event.message.strip().split()
        cmd_args.extend(args)

        if len(cmd_args) > 0:
            h = getattr(self, f'cmd_{cmd_args[0]}', None)
            if h:
                ret = await h(event, *cmd_args, **kwargs)
                return ret

    def _get_group_id(self, e: OneBotEvent, *args, **kwargs):
        gid = getattr(e, 'group_id', None)
        if not gid:
            return getattr(e, 'sender', {}).get('group_id')
        return gid


class UserProfile(models.Model):
    CERT_COLLEGE_ID = 1
    CERT_ADMIN = 1 << 1

    # user = models.OneToOneField('auth.User', on_delete=models.CASCADE, verbose_name='user')
    name = models.CharField(max_length=64, verbose_name='name')
    qq_number = models.PositiveIntegerField(verbose_name='qq')
    college = models.CharField(max_length=20, verbose_name='college name', default='YSU')
    grade = models.CharField(max_length=20, verbose_name='grade', default='')
    college_student_number = models.CharField(max_length=20, verbose_name='college student number')
    ctime = models.DateTimeField(auto_now_add=True)
    certificate = models.PositiveSmallIntegerField(verbose_name='cert', default=0)

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

    @classmethod
    def get_by_qq_number(cls, qq: int):
        return cls.objects.filter(qq_number=qq)

    @property
    def enrollment_year(self):
        if self.college_student_number.startswith('20'):
            return int(self.college_student_number[:4])
        else:
            return int(f'20{self.college_student_number[:2]}')


class PluginConfigs(models.Model):
    name = models.CharField(max_length=32, unique=True, verbose_name='name')
    verbose_name = models.CharField(max_length=32)
    configs = models.TextField()
    ctime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = 'PluginConfigs'
        ordering = ['-ctime', 'name', 'verbose_name']

    def __str__(self):
        return f'PluginConfigs(name={self.name})'

    @property
    def json_form_data(self):
        json_form_data = getattr(self, '_json_form_data', {})
        if json_form_data:
            return json_form_data

        # parse json form data
        if not self.configs:
            self.configs = '{}'
        else:
            ret = json.loads(self.configs)
        setattr(self, '_json_form_data', ret)
        return ret

