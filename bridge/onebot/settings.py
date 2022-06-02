from django.conf import settings


ONE_BOT = {
    'host': 'http://localhost:5700/',
    'access_token': 'cjh',
    'timeout': 5,   # in seconds
    'secret_key': 'cjh',
}

_onebot_settings = getattr(settings, 'ONE_BOT', None)
if isinstance(_onebot_settings, dict):
    ONE_BOT.update(_onebot_settings)

_status_to_errmsg = {
    200: '',
    401: 'onebot access_token not provided',
    403: 'onebot access_token not matched',
    406: 'onebot content-type not allowed',
    400: 'onebot content-type invalid',
    404: 'onebot api not found',
}


def get_errmsg_from_status(status: int) -> str:
    return _status_to_errmsg.get(status, 'onebot unexpected status: %d' % status)


EVENT_POST_TYPE_MESSAGE = 'message'
EVENT_POST_TYPE_MESSAGE_SENT = 'message_sent'
EVENT_POST_TYPE_NOTICE = 'notice'
EVENT_POST_TYPE_REQUEST = 'request'
EVENT_POST_TYPE_OTHER = 'other'
EVENT_POST_TYPE_META_INFO = 'meta_info'

EVENT_MESSAGE_TYPE_PRIVATE = 'private'
EVENT_MESSAGE_TYPE_GROUP = 'group'

EVENT_SUB_TYPE_FRIEND = 'friend'
EVENT_SUB_TYPE_GROUP = 'group'
EVENT_SUB_TYPE_GROUP_SELF = 'group_self'
EVENT_SUB_TYPE_OTHER = 'other'
EVENT_SUB_TYPE_NORMAL = 'normal'
EVENT_SUB_TYPE_ANONYMOUS = 'anonymous'
EVENT_SUB_TYPE_NOTICE = 'notice'


class PostType:
    MESSAGE = 'message'
    MESSAGE_SENT = 'message_sent'
    NOTICE = 'notice'
    REQUEST = 'request'
    OTHER = 'other'
    META_INFO = 'meta_info'


class MessageType:
    PRIVATE = 'private'
    GROUP = 'group'


class SubType:
    FRIEND = 'friend'
    GROUP = 'group'
    GROUP_SELF = 'group_self'
    OTHER = 'other'
    NORMAL = 'normal'
    ANONYMOUS = 'anonymous'
    NOTICE = 'notice'

