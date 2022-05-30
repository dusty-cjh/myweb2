import asyncio as aio
from django.test import TestCase
from asgiref.sync import async_to_sync as a2s
from common.utils import ErrCode
from .apis import OneBotApi, CQCode


class TestOneBotApi(TestCase):
    def setUp(self) -> None:
        pass

    def test_hello(self):
        cli = OneBotApi()
        params = {
            'user_id': 1157603107,
            'message': '嘤嘤嘤',
        }
        resp, err = a2s(cli.send_private_msg)(**params)
        self.assertEqual(ErrCode.SUCCESS, err)

        resp, err = a2s(cli.delete_msg)(**resp)
        self.assertEqual(ErrCode.SUCCESS, err)

    def test_with_field(self):
        cli = OneBotApi()

        resp, err = a2s(cli.with_fields(user_id=1157603107).send_private_msg)(message='hello')
        self.assertEqual(ErrCode.SUCCESS, err)

        resp, err = a2s(cli.delete_msg)(**resp)
        self.assertEqual(ErrCode.SUCCESS, err)

    def test_with_cache(self):
        cli = OneBotApi()

        resp, err = a2s(cli.get_group_info)(group_id=1143835437)
        self.assertEqual(ErrCode.SUCCESS, err)
        resp, err = a2s(cli.get_group_info)(group_id=1143835437)
        self.assertEqual(ErrCode.SUCCESS, err)
        cli = cli.with_cache(60)
        resp, err = a2s(cli.get_group_info)(group_id=1143835437)
        self.assertEqual(ErrCode.SUCCESS, err)
        resp, err = a2s(cli.get_group_info)(group_id=1143835437)
        self.assertEqual(ErrCode.SUCCESS, err)
        resp, err = a2s(cli.get_group_info)(group_id=1143835437)
        self.assertEqual(ErrCode.SUCCESS, err)
        resp, err = a2s(cli.get_group_info)(group_id=1143835437)
        self.assertEqual(ErrCode.SUCCESS, err)

        resp, err = a2s(cli.get_group_list)()
        self.assertEqual(ErrCode.SUCCESS, err)
        resp, err = a2s(cli.get_group_list)()
        self.assertEqual(ErrCode.SUCCESS, err)


class TestCQCode(TestCase):
    def setUp(self) -> None:
        pass

    def test_get_cqcode(self):
        expected = '[CQ:at,qq=114514]'
        self.assertEqual(expected, CQCode.at(114514))

        expected = '[CQ:at,qq=all]'
        self.assertEqual(expected, CQCode.at_all())

        expected = '[CQ:face,id=123]'
        self.assertEqual(expected, CQCode.face(123))
