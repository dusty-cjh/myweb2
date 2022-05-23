import traceback
from datetime import timedelta
import asyncio as aio
import ujson as json
import importlib
from functools import wraps
from typing import Callable
from asgiref.sync import sync_to_async as s2a
from django.db import models
from django.conf import settings
from common import utils


MAX_LIFETIME = settings.ASYNC_JOB.get('MAX_LIFETIME', 600)
MAX_RETRY = settings.ASYNC_JOB.get('MAX_RETRY', 3)


class Article(models.Model):
    STATUS_VISIBLE = 1
    STATUS_INVISIBLE = 2
    STATUS = (
        (STATUS_VISIBLE, '可见'),
        (STATUS_INVISIBLE, '不可见'),
    )

    TYPE_MD = 1
    TYPE_HTML = 2
    TYPES = (
        (TYPE_MD, 'markdown'),
        (TYPE_HTML, 'html'),
    )

    title = models.CharField(verbose_name='Title', max_length=50)
    content = models.TextField(verbose_name='Content', blank=False, null=False)
    content_type = models.PositiveSmallIntegerField(verbose_name='Content Type', choices=TYPES, default=TYPE_MD)
    author = models.ForeignKey(to='auth.User', on_delete=models.SET_NULL, verbose_name='author', null=True)
    status = models.PositiveSmallIntegerField(verbose_name='Status', choices=STATUS, default=STATUS_VISIBLE)
    created_time = models.DateTimeField(verbose_name='Created Time', auto_now_add=True)

    class Meta:
        ordering = ['-created_time']

    def __str__(self):
        return self.title


class PostBase(models.Model):
    STATUS_VISIBLE = 1
    STATUS_INVISIBLE = 2
    STATUS = (
        (STATUS_VISIBLE, '可见'),
        (STATUS_INVISIBLE, '不可见'),
    )

    title = models.CharField(verbose_name='标题', max_length=50)
    content = models.TextField(verbose_name='正文')
    status = models.PositiveSmallIntegerField(verbose_name='状态', choices=STATUS, default=STATUS_VISIBLE)
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        ordering = ['-created_time']
        abstract = True

    def __str__(self):
        return self.title


class Post(PostBase):
    class Meta:
        verbose_name = verbose_name_plural = '文章'


class Summary(models.Model):
    TYPE_POST = 1
    TYPE_PICT = 2
    TYPE_VIDEO = 3
    TYPE_AUDIO = 4
    TYPE_SHOP =5
    TYPE = (
        (TYPE_POST, '文章'),
        (TYPE_PICT, '照片'),
        (TYPE_VIDEO, '视频'),
        (TYPE_AUDIO, '音频'),
        (TYPE_SHOP, '商品'),
    )

    type = models.PositiveSmallIntegerField(verbose_name='类型', choices=TYPE)
    url = models.CharField(verbose_name='链接', max_length=200)
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    title = models.CharField(verbose_name='标题', max_length=50)
    desc = models.CharField(verbose_name='描述', max_length=200, default='', blank=True)
    recommend = models.BooleanField(verbose_name='是否推荐', default=False, help_text='如果作为推荐，则加入推荐系统')
    mainpage = models.BooleanField(verbose_name='是否首页可见', default=False, help_text='是否首页可见，否则只能在后台看到')
    preview = models.CharField(verbose_name='预览', help_text='图/音视频', max_length=200)
    uv = models.PositiveIntegerField(verbose_name='Unique Visitor', default=0)
    pv = models.PositiveIntegerField(verbose_name='Page View', default=0)

    class Meta:
        verbose_name = verbose_name_plural = '摘要'
        ordering = ['-created_time']

    def __str__(self):
        return self.title

    @classmethod
    def get_mainpage(cls):
        return cls.objects.filter(mainpage=True)

    @classmethod
    def get_recommend(cls):
        return cls.objects.filter(recommend=True)


class AsyncFuncJob(models.Model):
    # pending: job will run in next event loop
    # running:
    # pause:   job will not be discovered by event loop currently
    # fail:    failed by exception or set manually
    STATUS_PENDING = 1
    STATUS_RUNNING = 2
    STATUS_PAUSE = 3
    STATUS_FAIL = 4
    STATUS_SUCCESS = 5
    STATUS = (
        (STATUS_PENDING, 'pending'),
        (STATUS_RUNNING, 'running'),
        (STATUS_PAUSE, 'pause'),
        (STATUS_FAIL, 'fail'),
        (STATUS_SUCCESS, 'success'),
    )

    # job type selection
    JOB_TYPE_HELP = '1-is_coroutine, 2-has_sub_job, 4-is_sub_job'
    JOB_TYPE_IS_COROUTINE = 1
    JOB_TYPE_HAS_SUB_TASK = 1 << 1
    JOB_TYPE_IS_SUB_JOB = 1 << 2

    func_name = models.CharField(max_length=256, db_index=True)
    job_type = models.PositiveSmallIntegerField(verbose_name='job type', default=1, help_text=JOB_TYPE_HELP, blank=True)
    params = models.TextField(verbose_name='parameters')
    status = models.SmallIntegerField(choices=STATUS, default=STATUS_PENDING)

    max_retry = models.SmallIntegerField(default=3, verbose_name='max retry times')
    retries = models.SmallIntegerField(default=0, verbose_name='retry times count')
    max_lifetime = models.PositiveIntegerField(verbose_name='maximum lifetime', default=300)
    expire_time = models.DateTimeField(verbose_name='expire timestamp', help_text='default 5 min', blank=True)

    result = models.TextField(null=True, blank=True)
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='created timestamp')
    mtime = models.DateTimeField(verbose_name='modified timestamp', blank=True)

    class Meta:
        verbose_name = verbose_name_plural = 'AsyncFuncJob'
        ordering = ['-ctime', '-mtime', '-expire_time']

    def parse_params(self) -> dict:
        return json.loads(self.params)

    def parse_result(self) -> dict:
        if self.result:
            return json.loads(self.result)

    def set_params(self, data: dict):
        self.params = json.dumps(data)

    def set_result(self, data: dict, status=5):
        self.result = json.dumps(data)
        now = utils.get_datetime_now()
        updated = self.__class__.objects.filter(id=self.id, mtime=self.mtime).update(
            result=self.result,
            status=status,
            mtime=now,
        )
        if updated:
            self.mtime = now,
            self.status = status
            self.retries += 1

        return updated

    def set_error(self, err: dict, retry=False):
        self.result = json.dumps(err)
        now = utils.get_datetime_now()
        queryset = self.__class__.objects.filter(id=self.id, mtime=self.mtime)
        update_fields = dict(
            result=self.result,
            status=self.STATUS_FAIL,
            mtime=now,
        )
        if not retry:
            update_fields['retries'] = self.max_retry
        affected = queryset.update(**update_fields)
        if affected:
            self.mtime = now,
            self.status = self.STATUS_FAIL
            self.retries += 1

        return affected

    def _lock(self):
        now = utils.get_datetime_now()
        queryset = self.__class__.objects.filter(
            id=self.id,
            mtime=self.mtime,
            retries__lt=models.F('max_retry'),
        )
        affected = queryset.update(
            mtime=now,
            retries=models.F('retries') + 1,
            status=self.STATUS_RUNNING,
            expire_time=now + timedelta(seconds=self.max_lifetime),
        )
        self.mtime = now
        self.retries += 1
        self.status = self.STATUS_RUNNING
        self.expire_time = now + timedelta(seconds=self.max_lifetime)
        return affected

    def _import_func(self):
        path, func_name = self.func_name.rsplit('.', 1)
        module = importlib.import_module(path)
        func = getattr(module, func_name, None)
        if func is None:
            raise ImportError(f'package {path} have no function named: {func_name}')
        if not callable(func):
            raise ImportError(f'{self} function is not callable')

        return func

    def get_function(self):
        func = self._import_func()

        # async function decorator
        @wraps(func)
        def call(job: AsyncFuncJob, *args, **kwargs):
            # try to lock current func
            if not self._lock():
                return {
                    'error': f'{self} get_db_lock_failed',
                }

            # run func
            result = None
            try:
                result = func(job, *args, **kwargs)
            except Exception as e:
                result = {
                    'exception': repr(e),
                    'stack_info': traceback.format_exc(),
                }
                job.set_error(result, retry=True)
            else:
                if isinstance(result, dict):
                    job.set_result(result)
                else:
                    result = dict(data=repr(result))
                    job.set_result(result)

            return result

        return call

    def get_coroutine(self):
        func = self._import_func()

        # async function decorator
        @wraps(func)
        async def call(job: AsyncFuncJob, *args, **kwargs):
            # try to lock current func
            if not await s2a(self._lock)():
                return {
                    'error': f'{self} get_db_lock_failed',
                }

            # run func
            result = None
            try:
                result = await func(job, *args, **kwargs)
            except Exception as e:
                result = {
                    'exception': repr(e),
                }
                await s2a(job.set_error)(result, retry=True)
            except aio.TimeoutError:
                print('catched timeout error')
            else:
                if isinstance(result, dict):
                    await s2a(job.set_result)(result)
                else:
                    result = dict(data=repr(result))
                    await s2a(job.set_result)(result)

            return result

        return call

    @property
    def is_coroutine(self):
        return self.job_type & self.JOB_TYPE_IS_COROUTINE

    @property
    def has_sub_task(self):
        return self.job_type & self.JOB_TYPE_HAS_SUB_TASK

    def __str__(self):
        return f'AsyncFuncJob(id={self.id}, func={self.func_name})'

    @classmethod
    def get_callable_list(cls, limit=10):
        now = utils.get_datetime_now()
        queryset = cls.objects.filter(
            models.Q(
                status=cls.STATUS_PENDING,
            ) |
            models.Q(
                status=cls.STATUS_RUNNING,
                retries__lt=models.F('max_retry'),
                expire_time__lte=now,
            ) |
            models.Q(
                status=cls.STATUS_FAIL,
                retries__lt=models.F('max_retry'),
            )
        )

        return queryset

    @classmethod
    def create(cls, func: Callable, params: dict, job_type=None, expire_time=None,
               max_retry=MAX_RETRY, max_lifetime=MAX_LIFETIME):
        # set default value
        now = utils.get_datetime_now()
        if not job_type:
            job_type = cls.JOB_TYPE_IS_COROUTINE
        if not expire_time:
            expire_time = now + timedelta(seconds=max_lifetime)
        if isinstance(params, dict):
            params = json.dumps(params)

        # create
        import_name = get_func_import_name(func)
        obj = cls.objects.create(
            func_name=import_name,
            job_type=job_type,
            params=params,
            max_retry=max_retry,
            max_lifetime=max_lifetime,
            expire_time=expire_time,
            mtime=now,
        )
        return obj

    def safe_update(self, raise_exception=True, **update_fields) -> Exception:
        def handle_return(error):
            if raise_exception:
                raise error
            return error

        # global
        cls = self.__class__

        # validate
        now = utils.get_datetime_now()
        if self.expire_time <= now:
            err = TimeoutError(f'{repr(self)} has timeout')
            return handle_return(err)

        # update
        queryset = cls.objects.filter(
            id=self.id,
            mtime=self.mtime,
        )
        affected = queryset.update(**update_fields)
        if affected != 1:
            err = AssertionError(
                '%s safe_update failed, affected(%d) != 1, maybe because of timeout' % (repr(self), affected)
            )
            return handle_return(err)

        # set instance values
        for name, val in update_fields.items():
            setattr(self, name, val)


def get_func_import_name(func):
    return '{}.{}'.format(func.__module__, func.__name__)


async def create_async_coroutine_job(
        func: Callable,
        params: dict,
        expire_time=None,
        max_retry=MAX_RETRY,
        max_lifetime=MAX_LIFETIME,
):
    params = locals()
    params['job_type'] = AsyncFuncJob.JOB_TYPE_IS_COROUTINE
    return await s2a(AsyncFuncJob.create)(**params)
