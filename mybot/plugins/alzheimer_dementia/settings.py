from asgiref.sync import sync_to_async as s2a
from common.utils import serializer
from mybot.models import AbstractOneBotPluginConfig


class PluginConfig(AbstractOneBotPluginConfig):
    name = serializer.CharField(default='alzheimer_dementia')
    verbose_name = serializer.CharField(default='阿尔兹海默症')
    cmd_prefix = serializer.CharField(default='/')

    # notifications
    NOTI_ERROR = serializer.CharField(
        default='[alzheimer dementia] error\ngroup={group_id}\nplease try again or contact the administrator',
    )
    NOTI_STOP = serializer.CharField(
        default='[alzheimer dementia] stop\ngroup={group_id}\nthanks for using',
    )
    NOTI_ERROR_NO_PERMISSION = serializer.CharField(
        default='[alzheimer dementia] error\ncurrent bot has no permission on group {group_id}',
    )
    NOTI_RETRY = serializer.CharField(
        default='[alzheimer dementia] error\nstop running on {group_id} failed, please retry',
    )
    NOTI_RUNNING = serializer.CharField(
        default='[alzheimer dementia] running\nstart running on {group_id}\ninterval={interval}',
    )


async def get_latest_config() -> PluginConfig:
    return await s2a(PluginConfig.get_latest)()

