import ujson as json
from django.db import models


class AbstractPluginConfigs(models.Model):
    name = models.CharField(max_length=32, unique=True, verbose_name='name')
    verbose_name = models.CharField(max_length=32)
    configs = models.TextField()
    ctime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = 'AbstractPluginConfigs'
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
