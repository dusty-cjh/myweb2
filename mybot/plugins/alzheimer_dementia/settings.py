from common.utils import serializer
from mybot.models import AbstractOneBotPluginConfig


class PluginConfig(AbstractOneBotPluginConfig):
    verbose_name = serializer.CharField(default='阿尔兹海默症')
    cmd_prefix = serializer.CharField(default='/')

