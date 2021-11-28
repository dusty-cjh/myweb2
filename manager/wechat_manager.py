from django.conf import settings
from django.core.files.storage import Storage, FileSystemStorage, DefaultStorage
from wechatpy import WeChatClient, WeChatClientException, WeChatException, WeChatPay, WeChatOAuth
from wechatpy.session.redisstorage import RedisStorage
from redis import Redis

from . import utils


def get_wechat_client():
    # access token 持久化存储
    redis_client = Redis.from_url('redis://127.0.0.1:6379/0')
    session_interface = RedisStorage(
        redis_client,
        prefix="wechatpy"
    )

    client = WeChatClient(appid=settings.WECHAT['app_id'],
                          secret=settings.WECHAT['app_secret'],
                          session=session_interface)
    return client


def get_wechat_pay():
    pay = WeChatPay(appid=settings.WECHAT['app_id'],
                    api_key=settings.WECHAT['merchant_api_key'],
                    mch_id=settings.WECHAT['merchant_id'],
                    mch_cert=settings.WECHAT['merchant_cert'],
                    mch_key=settings.WECHAT['merchant_key'])
    return pay


def get_wechat_oauth():
    oauth = WeChatOAuth(
        app_id=settings.WECHAT['app_id'],
        secret=settings.WECHAT['app_secret'],
        redirect_uri=None,
        scope='snsapi_base',
        state='ytg',
    )
    return oauth


def wechat_oauth(scope='snsapi_base', redirect_url=None):
    if redirect_url == None:
        pass


@utils.dict_to_namedtuple(name='upload_image')
def upload_image(fp):
    client = get_wechat_client()
    resp = client.material.add('image', fp)
    return resp


@utils.dict_to_namedtuple(name='prepay_order')
def create_js_prepay_order(title, price: int, notify_url, openid, attach):
    pay = get_wechat_pay()
    order = pay.order.create(
        trade_type='JSAPI',
        body=title,
        total_fee=int(price * 100),
        notify_url=notify_url,
        user_id=openid,
        attach=str(attach),
    )

    params = pay.jsapi.get_jsapi_params(jssdk=True, prepay_id=order['prepay_id'])

    return params
