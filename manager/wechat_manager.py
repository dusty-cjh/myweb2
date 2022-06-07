from django.conf import settings
from django.http.request import HttpRequest
from django.utils.translation import gettext as _
from wechatpy import WeChatClient, WeChatClientException, WeChatException, WeChatPay, WeChatOAuth, parse_message
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.session.redisstorage import RedisStorage
from wechatpy.pay.api.refund import WeChatRefund
from redis import Redis

from . import utils, mock


def get_wechat_client():
    # access token 持久化存储
    session_interface = None
    if settings.ENV == 'live':
        redis_client = Redis.from_url(settings.CACHES['default']['LOCATION'])
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


@utils.dict_to_namedtuple(name='wechat_manager.upload_image')
@mock.return_fixed_data(data={
    "media_id": "labScUt_hDXAV75xvU6t_Jld1V1bZnMWilG63QRLplLHvwSdnv6CAavb9hNBcTOq",
    "url": "http://mmbiz.qpic.cn/mmbiz_png/u3QOfMCy8qicKF9oq7lludYsDw42j1wpcPwEZnn5SlIJ3SsLfNm1M87ZLNgnRYHbymxOtMQy2y5PlyicIgaAGV0Q/0?wx_fmt",
    "item": [],
    "errcode": 0,
    "errmsg": "success"
})
def upload_image(fp):
    client = get_wechat_client()
    resp = client.material.add('image', fp)
    return resp


@utils.dict_to_namedtuple(name='wechat_manager.prepay_order')
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


def parse_wechat_message(request: HttpRequest):
    if not settings.WECHAT['is_crypto']:
        return parse_message(request.body)

    crypto = WeChatCrypto(settings.WECHAT['token'], settings.WECHAT['aes_key'], settings.WECHAT['app_id'])
    xml = request.body
    msg_signature = request.GET.get('msg_signature')
    timestamp = request.GET.get('timestamp')
    nonce = request.GET.get('nonce')

    try:
        decrypted_xml = crypto.decrypt_message(
            xml,
            msg_signature,
            timestamp,
            nonce
        )
    except (InvalidAppIdException, InvalidSignatureException):
        pass
    else:
        msg = parse_message(decrypted_xml)
        request.log.info('wechat_manager.parse_wechat_message|message={}', msg)
        return msg


@utils.dict_to_namedtuple(name='wechat_manager.wechatpay_refund')
def wechatpay_refund(refund_fee, out_trade_no):
    refund = get_wechat_pay().refund
    ret = refund.apply(
        total_fee=refund_fee, refund_fee=refund_fee,
        out_trade_no=out_trade_no, out_refund_no=out_trade_no,
    )
    return ret


@utils.dict_to_namedtuple(name='wechat_manager.wechatpay_redpack')
def wechatpay_redpack(
        user_id, total_amount,
        send_name=_('dusty-hjc'), act_name=_('gift'), wishing=_('Best wishes'),
        remark='', client_ip='', total_num=1, scene_id='',
):
    params = {k: v for k, v in locals().items()}
    pay = get_wechat_pay()
    ret = pay.redpack.send(**params)
    return ret

