import ujson as json
import asyncio as aio
import threading
import traceback
from concurrent import futures
from asgiref.sync import async_to_sync as a2s
from datetime import datetime, timedelta
from django.test import TestCase
from common import utils
from common.tests import tell_now, atell_now, raise_exception, hello
from post.models import AsyncFuncJob, get_func_import_name


class AsyncFuncTestCase(TestCase):
    def setUp(self):
        now = utils.get_datetime_now()
        self.j1 = AsyncFuncJob.create(tell_now, {"msg": "hello~ midnight:"}).id
        self.j2 = AsyncFuncJob.create(tell_now, {"msg": "hello~ midnight:", "fail": 1}, max_retry=2).id
        self.j3 = AsyncFuncJob.create(tell_now, {"msg": "test_race_competition:", "delay": 3}, max_retry=2).id
        self.j4 = AsyncFuncJob.create(atell_now, {"msg": "hello~ midnight:"}).id
        self.j5 = AsyncFuncJob.create(raise_exception, {"msg": "hello exception"}).id

    def test_runnable(self):
        # lion = Animal.objects.get(name="lion")
        # cat = Animal.objects.get(name="cat")
        # self.assertEqual(lion.speak(), 'The lion says "roar"')
        # self.assertEqual(cat.speak(), 'The cat says "meow"')
        job = AsyncFuncJob.objects.get(id=self.j1)
        print(job)
        func = job.get_function()
        resp = func(job)
        print('resp:', resp)

        job = AsyncFuncJob.objects.get(id=job.id)
        self.assertEqual(job.status, job.STATUS_SUCCESS)
        self.assertEqual(job.retries, 1)

    def test_retry(self):
        # run failed
        job = AsyncFuncJob.objects.get(id=self.j2)
        func = job.get_function()
        resp = func(job)
        print('resp:', resp)

        job = AsyncFuncJob.objects.get(id=job.id)
        self.assertEqual(job.status, job.STATUS_FAIL)
        self.assertEqual(job.retries, 1)

        resp = job.get_function()(job)
        self.assertIn('exception', resp, 'exception not in resp')

        job = AsyncFuncJob.objects.get(id=job.id)
        resp = job.get_function()(job)
        self.assertIn('get_db_lock_failed', resp.get('error', ''), 'error not in resp')

    def test_race_condition(self):
        # global
        max_workers = 5
        job = AsyncFuncJob.objects.get(id=self.j3)

        def run_task(job: AsyncFuncJob):
            func = job.get_function()
            result = func(job)
            return result

        with futures.ThreadPoolExecutor(max_workers) as executor:
            res = executor.map(run_task, (job, ) * max_workers)
            for i, resp in enumerate(res, 1):
                print('work-{} result: {}'.format(i, resp))

    def test_async_func(self):
        job = AsyncFuncJob.objects.get(id=self.j4)
        func = job.get_coroutine()
        aio.run(func(job))

        # check
        job = AsyncFuncJob.objects.get(id=self.j4)
        self.assertEqual(job.status, job.STATUS_SUCCESS)
        self.assertEqual(job.retries, 1)

    def test_get_function_full_import_path(self):
        name = get_func_import_name(utils.get_datetime_now)
        self.assertEqual(name, 'common.utils.utils.get_datetime_now')

    def test_catch_exception(self):
        job = AsyncFuncJob.objects.get(id=self.j5)
        func = job.get_function()
        resp = func(job)
        print('resp:', resp)
        job = AsyncFuncJob.objects.get(id=job.id)
        self.assertEqual(job.status, job.STATUS_FAIL)


class AsyncCoroutineDecoratorTestCase(TestCase):
    def setUp(self):
        now = utils.get_datetime_now()
        self.j1 = a2s(hello.add_job)('cjh', echo='fuck u too').id

    def test_hello(self):
        job = AsyncFuncJob.objects.get(id=self.j1)

        # call coroutine job
        coro = job.get_coroutine()
        resp = a2s(coro)(job)
        self.assertEqual(resp, 'fuck u too')

        # call original function
        resp = a2s(hello)(None, 'hd', echo='hi beauty')
        self.assertEqual('hi beauty', resp)


def create_ysu_check_job(user_id, group_id):
    params = locals()
    now = utils.get_datetime_now()
    obj = AsyncFuncJob.objects.create(
        func_name='mybot.plugins.auto_approve.ysu_check_job',
        job_type=AsyncFuncJob.JOB_TYPE_IS_COROUTINE,
        params=json.dumps(params),
        expire_time=now+timedelta(seconds=300),
        mtime=now,
    )
    return obj
