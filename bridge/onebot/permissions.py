from .event import OneBotEvent
from . import settings as constants


def message_from_manager(event: OneBotEvent, *args, **kwargs):
    return event.sender and constants.Role.is_manager(event.sender.role)


