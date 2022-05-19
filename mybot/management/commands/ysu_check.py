import asyncio as aio
from asgiref.sync import async_to_sync as a2s
from django.core.management.base import BaseCommand, CommandError
from post.models import AsyncFuncJob
from mybot.plugins.auto_approve import get_username_by_school_id, ysu_check


"""
    ref: https://docs.python.org/3/library/argparse.html#module-argparse
"""

HALF_DAY = 3600 * 12
ONE_DAY = HALF_DAY * 2


class Command(BaseCommand):
    help = 'YSU user info checker'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=str)
        parser.add_argument('--job')

    def handle(self, *args, **options):
        # insert job
        job = options.get('job')
        if job:
            args = job.split(',')
            if len(args) != 2:
                raise CommandError('invalid job arguments, usage: --job <qq_number>,<qq_group_number>')
            try:
                args = [int(x) for x in args]
            except Exception as e:
                raise CommandError('job arguments must be integer, usage: --job <qq_number>,<qq_group_number>')
            job = self.insert_ysu_check_job(*args)
            self.stdout.write(self.style.SUCCESS(f'{job} inserted'))

        # check user
        ysu_id = options.get('id')
        if ysu_id:
            try:
                uname = a2s(get_username_by_school_id)(ysu_id)
            except Exception as e:
                raise CommandError('got exception while running: %s' % repr(e))
            self.stdout.write(self.style.SUCCESS('{}-{}'.format(ysu_id, uname)))

    def insert_ysu_check_job(self, user_id, group_id):
        ysu_check.add_job(user_id, group_id)
        # return AsyncFuncJob.create(
        #     ysu_check_job, {
        #         'user_id': user_id,
        #         'group_id': group_id,
        #     },
        #     max_lifetime=ONE_DAY,
        # )
