import os
from django.apps import AppConfig

from .models import MATERIAL_ROOT, MATERIAL_URL


class ConfigConfig(AppConfig):
    name = 'config'
    verbose_name = verbose_name_plural = '站点配置'

    def ready(self):
        if not os.path.exists(MATERIAL_ROOT):
            os.makedirs(MATERIAL_ROOT)
