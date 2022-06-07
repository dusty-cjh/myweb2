import asyncio as aio
from datetime import datetime, timedelta
from django.core.cache import cache
from common import utils
from bridge.onebot import Role, PostType, MessageType, SubType
from post.decorators import async_coroutine, AsyncFuncContext
from mybot.manager import OneBotPrivateMessageSession
from mybot.models import OneBotEventTab
from .settings import get_latest_config


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


@async_coroutine(max_lifetime=3600 * 24 * 365)
async def recall_message(ctx: AsyncFuncContext, operator: int, group: int, interval: int):
    # global
    log = ctx.log
    session = OneBotPrivateMessageSession(operator, group)
    cli = session.api
    cfg = await get_latest_config()
    cache_key = 'ajob.{}.recall_message'.format(ctx.job.id)
    sleep_time = max(interval / 10, 10)
    start_time = utils.get_datetime_now() - timedelta(seconds=interval)

    # validate
    info, err = await cli.with_cache(60).with_max_retry(3).get_group_member_info(group, operator)
    if err:
        log.error('recall message get group member info failed, err={}, resp={}', err, info)
        await cli.send_private_msg(cfg.NOTI_ERROR.format(group_id=group), operator, group)
        return
    if not Role.is_manager(info['role']):
        log.error('recall message | user {} is not admin in {}', operator, group)
        await cli.send_private_msg(cfg.NOTI_ERROR_NO_PERMISSION.format(group_id=group))
        return

    # stop
    log.info('handle alzheimer:{}', (operator, group, interval))
    if interval == 0:
        # stop forget
        if await cache.adelete(cache_key):
            await cli.send_private_msg(cfg.NOTI_STOP.format(group_id=group), operator, group)
        log.info('alzheimer gonna be stopped')
        return

    # start
    while True:
        # recall message list
        msg_id_list = OneBotEventTab.objects.filter(
            post_type__in=(PostType.MESSAGE, PostType.MESSAGE_SENT),
            message_type=MessageType.GROUP,
            sub_type=SubType.NORMAL,
            group_id=group,
            time__gte=start_time,
        ).order_by('-time')[:9].values_list('message_id')
        print(msg_id_list)
        for args in msg_id_list:
            msg_id = args[0]
            await cli.delete_msg(msg_id)
            await aio.sleep(1)

        # check whether valid
        await aio.sleep(sleep_time)
        if not await cache.ahas_key(cache_key):
            break

    log.info('alzheimer handler has stopped')
