from common.utils import serializer
from mybot.models import AbstractOneBotPluginConfig


class PluginConfig(AbstractOneBotPluginConfig):
    verbose_name = serializer.CharField(default='基础命令')
    cmd_prefix = serializer.CharField(default='/')
    groups = []
