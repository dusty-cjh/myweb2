from django.conf import settings

ONE_BOT = {
    'host': 'http://localhost:5700',
    'access_token': 'cjh',
    'timeout': 5,   # in seconds
    'secret_key': 'cjh',
}

ONE_BOT_SETTINGS = getattr(settings, 'ONE_BOT', None)
if isinstance(ONE_BOT_SETTINGS, dict):
    ONE_BOT.update(ONE_BOT_SETTINGS)


class OneBotApiConfig:
    send_private_msg = '{host}/send_private_msg'.format(host=ONE_BOT['host'])

