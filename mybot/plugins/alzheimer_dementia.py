from asgiref.sync import async_to_sync as a2s
from bridge.onebot import AsyncOneBotApi, OneBotApi, AbstractOneBotEventHandler, OneBotCmdMixin, create_event
from post.decorators import async_coroutine, AsyncFuncContext
from mybot.models import AbstractOneBotPluginConfig, serializer
from mybot.manager import OneBotPrivateMessageSession


class PluginConfig(AbstractOneBotPluginConfig):
    verbose_name = serializer.CharField(default='阿尔兹海默症')
    cmd_prefix = serializer.CharField(default='/')


class OneBotEventHandler(AbstractOneBotEventHandler, OneBotCmdMixin):
    pass


@async_coroutine()
async def echo(ctx: AsyncFuncContext, qq, group=None):
    # global
    log = ctx.log
    session = OneBotPrivateMessageSession(qq)
    session.api = session.api.with_fields(user_id=qq, group_id=group)

    await session.api.send_private_msg('Hello echoing, timeout in 30 seconds')
    while msg := await session.get_message(30):
        if msg is None:
            break

        await session.api.send_private_msg(message='echo ' + msg.message)

    await session.api.send_private_msg('Bye~')
