import asyncio as aio
from asgiref.sync import async_to_sync as a2s
from django.core.management.base import BaseCommand, CommandError
from mybot.plugins.auto_approve import get_username_by_school_id


class Command(BaseCommand):
    help = 'YSU user info checker'

    def add_arguments(self, parser):
        parser.add_argument('id', nargs='+', type=str)

    def handle(self, *args, **options):
        ysu_id = options['id'][0]
        try:
            uname = a2s(get_username_by_school_id)(ysu_id)
        except Exception as e:
            raise CommandError('got exception while running: %s' % repr(e))
        self.stdout.write(self.style.SUCCESS('{}-{}'.format(ysu_id, uname)))
