from django.conf import settings

ONE_BOT = {
    'host': 'http://localhost:5700/',
    'access_token': 'cjh',
    'timeout': 5,   # in seconds
    'secret_key': 'cjh',
    'max_retry': 3,
}

ONE_BOT_SETTINGS = getattr(settings, 'ONE_BOT', None)
if isinstance(ONE_BOT_SETTINGS, dict):
    ONE_BOT.update(ONE_BOT_SETTINGS)
