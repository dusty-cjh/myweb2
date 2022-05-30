from asgiref.sync import async_to_sync, sync_to_async
from django.test import TestCase
from .onebot.apis import OneBotApi, get_response
from .onebot.settings import OneBotApiConfig
from .plugins.auto_approve import get_username_by_school_id
from . import tasks


class TestOneBotApi(TestCase):
    def setUp(self):
        pass

    def test_send_private_message(self):
        params = {
            'user_id': 2111292071,
            'message': '嘤嘤嘤',
        }
        data = async_to_sync(OneBotApi.send_private_msg)(**params)
        # async_to_sync(OneBotApi.delete_msg)()
        print(data.retcode)
        pass

    def test_get_username_by_id(self):
        userid = '160107020099'
        data = async_to_sync(get_username_by_school_id)(userid)
        print(data)


class TestCeleryApi(TestCase):
    def setUp(self) -> None:
        pass

    def test_celery_add(self):
        res = tasks.add.delay(2, 2)
        self.assertEqual(4, res.get())
