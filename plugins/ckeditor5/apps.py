from django.apps import AppConfig

from plugins import ckeditor5


class Ckeditor5Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.ckeditor5'
