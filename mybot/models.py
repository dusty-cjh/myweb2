import random
import ujson as json
from collections import namedtuple
from typing import Callable, List, Iterable
from datetime import datetime, timedelta
from django.db import models
from django.http.request import HttpRequest
from django.db.models import Q, F, Func, Value
from django.contrib.auth.models import User
from django.conf import settings
from bridge.onebot import OneBotEvent, constants
from common.middlewares import LoggingContextAdapter
from common.utils import serializer
from common import utils

CLASS_NAME_PLUGIN_CONFIG = 'PluginConfig'


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


class OneBotEventTab(models.Model):
    POST_TYPE_MESSAGE = 'message'
    POST_TYPE_REQUEST = 'request'
    POST_TYPE_NOTICE = 'notice'
    POST_TYPE_META_EVENT = 'meta_event'
    POST_TYPE_MESSAGE_SENT = 'message_sent'
    POST_TYPE = (
        (POST_TYPE_MESSAGE, POST_TYPE_MESSAGE,),
        (POST_TYPE_REQUEST, POST_TYPE_REQUEST,),
        (POST_TYPE_NOTICE, POST_TYPE_NOTICE,),
        (POST_TYPE_META_EVENT, POST_TYPE_META_EVENT,),
        (POST_TYPE_MESSAGE_SENT, POST_TYPE_MESSAGE_SENT),
    )

    MESSAGE_TYPE_GROUP = 'group'
    MESSAGE_TYPE_PUBLIC = 'public'
    MESSAGE_TYPE_PRIVATE = 'private'
    MESSAGE_TYPE = (
        (MESSAGE_TYPE_GROUP, MESSAGE_TYPE_GROUP,),
        (MESSAGE_TYPE_PUBLIC, MESSAGE_TYPE_PUBLIC,),
        (MESSAGE_TYPE_PRIVATE, MESSAGE_TYPE_PRIVATE,),
    )

    SUB_TYPE_PRIVATE = 'private'
    SUB_TYPE_FRIEND = 'friend'
    SUB_TYPE_GROUP = 'group'
    SUB_TYPE_OTHER = 'other'
    SUB_TYPE_ANONYMOUS = 'anonymous'
    SUB_TYPE_NOTICE = 'notice'
    SUB_TYPE_NORMAL = 'normal'
    SUB_TYPE = (
        (SUB_TYPE_PRIVATE, SUB_TYPE_PRIVATE,),
        (SUB_TYPE_FRIEND, SUB_TYPE_FRIEND,),
        (SUB_TYPE_GROUP, SUB_TYPE_GROUP,),
        (SUB_TYPE_OTHER, SUB_TYPE_OTHER,),
        (SUB_TYPE_ANONYMOUS, SUB_TYPE_ANONYMOUS,),
        (SUB_TYPE_NORMAL, SUB_TYPE_NORMAL,),
        (SUB_TYPE_NOTICE, SUB_TYPE_NOTICE,),
    )

    time = models.DateTimeField()
    self_id = models.PositiveIntegerField()
    post_type = models.CharField(max_length=20, choices=POST_TYPE)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE)
    sub_type = models.CharField(max_length=20, default='', choices=SUB_TYPE)
    message_id = models.IntegerField()
    user_id = models.PositiveIntegerField()
    message = models.TextField(null=True)
    raw_message = models.TextField(null=True)
    font = models.IntegerField(default=0)
    sender = models.TextField(null=True)
    group_id = models.PositiveIntegerField(default=0)
    anonymous = models.TextField(null=True)

    class Meta:
        ordering = ['-time', ]
        verbose_name = verbose_name_plural = 'QQ Message'

    def __str__(self):
        return 'OneBotEventTab(message_id=%d)' % self.message_id

    @classmethod
    def save_message(cls, raw_message: dict):
        params = {}
        # print('distinct:', set(raw_message.keys()) ^ set([x.name for x in cls._meta.fields]))
        for field in cls._meta.fields:
            key = field.name
            if key not in raw_message:
                continue

            value = raw_message[key]

            # transform data format
            if isinstance(field, models.DateTimeField):
                value = datetime.fromtimestamp(value, tz=settings.PY_TIME_ZONE)
            elif isinstance(value, dict):
                value = json.dumps(value)
            params[field.name] = value

        return cls.objects.create(**params)
