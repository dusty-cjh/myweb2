from .event import OneBotEvent
from . import settings as constants


def message_from_manager(event: OneBotEvent, *args, **kwargs):
    return event.sender and constants.Role.is_manager(event.sender.role)


def is_message(event: OneBotEvent, *args, **kwargs):
    return event.post_type in (constants.PostType.MESSAGE, constants.PostType.MESSAGE_SENT)


def is_group_message(event: OneBotEvent, *args, **kwargs):
    return is_message(event, *args, **kwargs) and event.message_type == constants.MessageType.GROUP


def is_private_message(event: OneBotEvent, *args, **kwargs):
    return is_message(event, *args, **kwargs) and event.message_type == constants.MessageType.PRIVATE


class BasePermission:
    def __init__(self, func=None):
        if func:
            self.check_permission = func

    def check_permission(self, event: OneBotEvent, *args, **kwargs):
        return True

    def __call__(self, event: OneBotEvent, *args, **kwargs):
        return True

    def __and__(self, other):
        func = lambda event, *args, **kwargs: self(event, *args, **kwargs) and other(event, *args, **kwargs)
        return func

    def __or__(self, other):
        func = lambda event, *args, **kwargs: self(event, *args, **kwargs) or other(event, *args, **kwargs)
        return func

