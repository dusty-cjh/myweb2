from django import forms
from django.utils.translation import gettext as _
from bridge.onebot.django_extension import OnebotGroupMultiChoiceField
from common.utils import serializer
from mybot.models import AbstractOneBotPluginConfig


def get_text_field(help_text=None, widget=forms.Textarea(attrs=dict(cols=80))):
    class TextField(forms.CharField):
        nonlocal help_text, widget

    return TextField


class PluginConfig(AbstractOneBotPluginConfig):
    name = serializer.CharField(default='base_command')
    verbose_name = serializer.CharField(default='基础命令')
    cmd_prefix = serializer.CharField(default='/')

    # switches
    AUTO_APPROVE_INTERVAL = serializer.IntField(verbose_name='auto-approve interval between requests', default=30)
    AUTO_APPROVE_GROUP_ADD_REQUEST = serializer.SetField(
        verbose_name=_('auto-approve group add request'),
        default=[],
        django_form_field=OnebotGroupMultiChoiceField,
    )
    AUTO_APPROVE_FRIEND_ADD_REQUEST = serializer.BooleanField(
        verbose_name=_('auto-approve friend add request'),
        default=True,
        django_form_field=forms.BooleanField,
    )

    #
    NEW_FRIEND_GREETING = serializer.CharField(
        verbose_name='new-friend greeting',
        default='',
    )

    # noti message
    MESSAGE_AUTO_REPLY = serializer.CharField(
        verbose_name=_('noti: auto-reply-while-friend-message'),
        default=_(''),
    )


class CacheKey:
    AUTO_APPROVE_GRUOP_ADD = 'auto-approve.grp.add.latest_timestamp'
    AUTO_APPROVE_FRIEND_ADD = 'auto-approve.fred.add.latest_timestamp'

