import ujson as json
from datetime import datetime, timedelta
from django.db import models
from django.db.models import Q, F, Func, Value
from django.contrib.auth.models import User
from django.conf import settings
from bridge.onebot import AbstractOneBotPluginConfig as BridgeAbstractOneBotPluginConfig
from bridge.onebot import AbstractPluginConfigs


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


class PluginConfigs(AbstractPluginConfigs):
    class Meta:
        verbose_name = verbose_name_plural = 'PluginConfigs'

    def __str__(self):
        return f'PluginConfigs(name={self.name})'


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


class AbstractOneBotPluginConfig(BridgeAbstractOneBotPluginConfig):
    plugin_config_model = PluginConfigs
