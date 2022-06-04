from common.utils import serializer
from mybot.models import AbstractOneBotPluginConfig


class PluginConfig(AbstractOneBotPluginConfig):
    name = serializer.CharField(default='base_command')
    verbose_name = serializer.CharField(default='基础命令')
    cmd_prefix = serializer.CharField(default='/')
    groups = []
