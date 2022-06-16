import ujson as json
import cachetools
from django.db import models
from django.utils.translation import gettext as _
from .settings import ONE_BOT


class AbstractPluginConfigs(models.Model):
    name = models.CharField(max_length=32, unique=True, verbose_name='name')
    verbose_name = models.CharField(max_length=32)
    configs = models.TextField()
    ctime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = _('AbstractPluginConfigs')
        ordering = ['-ctime', 'name', 'verbose_name']
        abstract = True

    def __str__(self):
        return f'PluginConfigs(name={self.name})'

    @property
    def json_form_data(self):
        json_form_data = getattr(self, '_json_form_data', {})
        if json_form_data:
            return json_form_data

        # parse json form data
        if not self.configs:
            self.configs = '{}'
        else:
            ret = json.loads(self.configs)
        setattr(self, '_json_form_data', ret)
        return ret

    def get_configs(self) -> dict:
        return json.loads(self.configs)


class AbstractOneBotApiConfig(models.Model):
    HTTP_SCHEMA_GENERAL = 'http'
    HTTP_SCHEMA_ENCRYPTED = 'https'
    HTTP_SCHEMA = (
        (HTTP_SCHEMA_GENERAL, 'http'),
        (HTTP_SCHEMA_ENCRYPTED, 'https'),
    )
    self_id = models.PositiveIntegerField(verbose_name=_('robot id'), null=False, blank=False, editable=False)
    host = models.CharField(max_length=200, verbose_name=_('host'))
    port = models.PositiveIntegerField(verbose_name='port', default=5700)
    http_schema = models.CharField(
        max_length=5, verbose_name='http schema', choices=HTTP_SCHEMA, default=HTTP_SCHEMA_GENERAL)
    timeout = models.PositiveIntegerField(verbose_name=_('api timeout'), default=15)
    cache_timeout = models.PositiveIntegerField(verbose_name=_('cache expire time'), default=60)
    access_token = models.CharField(
        max_length=200, verbose_name=_('access token'), blank=True, default=ONE_BOT.get('access_token', ''))
    max_retry = models.PositiveIntegerField(verbose_name=_('max retry'), default=3)
    sort_weight = models.PositiveSmallIntegerField(verbose_name='sort weight', default=1)

    class Meta:
        verbose_name = verbose_name_plural = _('AbstractOneBotApiConfig')
        ordering = ['host']
        abstract = True
        unique_together = 'self_id host port'.split()
        index_together = 'self_id host port'.split()

    @classmethod
    @cachetools.cached(cache=cachetools.TTLCache(maxsize=200, ttl=60))
    def get_by_self_id(cls, self_id):
        try:
            obj = cls.objects.filter(self_id=self_id).first()
        except cls.DoesNotExist:
            pass
        else:
            return obj

    def __str__(self):
        return f'api_config({self.self_id})'
