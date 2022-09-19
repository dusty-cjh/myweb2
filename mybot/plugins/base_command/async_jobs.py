import random
import asyncio as aio
from common import utils
from datetime import datetime
from post.decorators import async_coroutine, AsyncCoroutineFuncContext
from bridge.onebot import PostType, CQCode, Role, AsyncOneBotApi, MessageType


@async_coroutine(max_lifetime=360 * 25)
async def clean_group_diver(
		ctx: AsyncCoroutineFuncContext,
		group_id: int, *args, diving_days=365, max_kick=100, **kwargs
):
	log = ctx.log
	api = AsyncOneBotApi().with_max_retry(1)
	member_list, err = await api.get_group_member_list(group_id, no_cache=ctx.job.retries)
	if err:
		log.error('api.get_group_member_list failed, err={}', err)
	else:
		log.error('api.get_group_member_list success, member count: {}', len(member_list))

	# get all dead fish
	now = utils.get_datetime_now().timestamp()
	dead_fish = []
	for member in member_list:
		userid, join_time, last_sent_time = member['user_id'], member['join_time'], member['last_sent_time']

		if last_sent_time + diving_days * 3600 * 24 < now:
			dead_fish.append(member)
	log.info('dead fish count={}, max_kick={}, dead fish list={}', len(dead_fish), max_kick, dead_fish)
	dead_fish = dead_fish[:max_kick]

	# clean dead fish
	cleaned_count = 0
	for member in dead_fish:
		userid = member['user_id']
		info = 'Hi, This message is from auto cleaner\nyou have not speak for more than a year, so we will kick you out of group.\nYou can resend join request later.'
		info += '\n' + str(random.random())
		# await api.send_private_msg(info, userid, group_id)	# too easy to be banned
		resp, err = await api.set_group_kick(group_id, userid)
		if not err:
			cleaned_count += 1
		log.info(
			'dead fish progress: {}-{}-{}, userid={}, nickname={}, group_id={}, join_time={}, last_sent_time={}',
			cleaned_count, len(dead_fish), len(member_list), userid, member['nickname'], group_id,
			member['join_time'], member['last_sent_time'],
		)
		log.info('deash fisn fiafe, resp={}', resp)
		await aio.sleep(7 + random.random() * 5)

	#  cleaned / dead count / total
	log.info('task success, result={}-{}-{}', cleaned_count, len(dead_fish), len(member_list))
	return '{}-{}-{}'.format(cleaned_count, len(dead_fish), len(member_list), )
