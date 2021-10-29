import time
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.core.cache import cache
from django.http.response import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from rest_framework.response import Response
from rest_framework import status

from wechatpy.exceptions import InvalidSignatureException
from wechatpy.utils import check_signature
from wechatpy.pay import WeChatPay
from wechatpy.client import WeChatClient
from wechatpy.oauth import WeChatOAuth, WeChatOAuthException
from wechatpy.session.redisstorage import RedisStorage
from redis import Redis


class WeChatCommonMixin:
    wxcfg = settings.WECHAT

    # access token 持久化存储
    redis_client = Redis.from_url('redis://127.0.0.1:6379/0')
    session_interface = RedisStorage(
        redis_client,
        prefix="wechatpy"
    )

    client = WeChatClient(appid=wxcfg['app_id'],
                          secret=wxcfg['app_secret'],
                          session=session_interface)
    pay = WeChatPay(appid=wxcfg['app_id'],
                    sub_appid=wxcfg['app_id'],
                    api_key=wxcfg['merchant_api_key'],
                    mch_id=wxcfg['merchant_id'],
                    mch_cert=wxcfg['merchant_cert'],
                    mch_key=wxcfg['merchant_key'])


class WeChatPayResultMixin(WeChatCommonMixin):
    """
    建议实现：
       pay_valid(result)   -> None
       pay_invalid(result) -> None
    """
    result = None

    def post(self, request, *args, **kwargs):
        """
        支付及返回结果参考文档：
            https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_7
        """

        try:
            result = self.pay.parse_payment_result(request.body)
        except InvalidSignatureException:
            return Response('签名不合法！', status=status.HTTP_400_BAD_REQUEST)
        else:
            self.result = result

        try:
            if result['result_code'] == 'SUCCESS':
                self.pay_valid(result)
            else:
                self.pay_invalid(result)
        except Exception as err:
            pass

        return HttpResponse(b'<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>',
                            content_type='text/xml',
                            status=200)

    def pay_valid(self, result):
        # 对该订单号进行处理
        print('WeChatAPI: 订单{}已支付{}分，微信订单号为：{}'.format(result['out_trade_no'], result['cash_fee'], result['transaction_id']))

    def pay_invalid(self, result):
        # 对该订单号进行处理
        print('WeChatAPI: 订单{}异常：{}'.format(result['out_trade_no'], result['return_msg']))


class TokenCheckMixin(WeChatCommonMixin):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        signature = request.GET.get('signature', '')
        timestamp = request.GET.get('timestamp', '')
        nonce = request.GET.get('nonce', '')
        try:
            check_signature(self.wxcfg['token'], signature, timestamp, nonce)
        except InvalidSignatureException:
            return HttpResponseForbidden('WeChat Token Validate Failure')

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return HttpResponse(request.GET['echostr'], status=200)


class WeChatPayMixin:
    """
    需要 context 含 request
    需要 form 含 [js]window.location.href
    """
    wxcfg = settings.WECHAT
    client = WeChatClient(appid=wxcfg['app_id'],
                          secret=wxcfg['app_secret'])
    pay = WeChatPay(appid=wxcfg['app_id'],
                    sub_appid=wxcfg['app_id'],
                    api_key=wxcfg['merchant_api_key'],
                    mch_id=wxcfg['merchant_id'],
                    mch_cert=wxcfg['merchant_cert'],
                    mch_key=wxcfg['merchant_key'])

    # 微信支付 href
    href = ''
    params = None

    def create_prepay(self, total_fee, notify_url, out_trade_no=None,
                      trade_body='', trade_detail='', attach=None, href=None):

        request = self.context['request']
        timestamp = int(time.time())
        user_id = request.user.username

        #
        if href:
            self.href = href

        # 修正 notify url
        if notify_url.startswith('/'):
            notify_url = '{scheme}://{host}{path}'.format(scheme=request.scheme,
                                                          host=request.get_host(),
                                                          path=notify_url)

        # 预付单
        order = self.pay.order.create(trade_type='JSAPI',
                                      body=trade_body,
                                      total_fee=int(total_fee),
                                      notify_url=notify_url,
                                      user_id=user_id,
                                      sub_user_id=user_id,
                                      out_trade_no=out_trade_no,
                                      detail=trade_detail,
                                      attach=attach)
        # 获取 JS-SDK 在微信支付过程中需要用到的参数
        js_params = self.pay.jsapi.get_jsapi_params(prepay_id=order['prepay_id'],
                                                    timestamp=timestamp,
                                                    nonce_str=order['nonce_str'],
                                                    jssdk=True)

        """  
        参考文档：https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/JS-SDK.html#62
        url（当前网页的URL，不包含#及其后面部分）
        当当前url中含有GET字段时，在微信开发者工具中会报错(wx.error有值)，但在我的微信中无报错(wx.error 中代码未调用)，且支付成功。
        """
        # JSAPI 初始化请求需要用到的signature
        signature = self.client.jsapi.get_jsapi_signature(order['nonce_str'],
                                                          self.client.jsapi.get_jsapi_ticket(),
                                                          timestamp,
                                                          self.href)

        # 更新params
        self.params = {
            'js_params': js_params,
            'signature': signature,
        }
        return self.params


class OAuthMixin(WeChatCommonMixin):
    """ 请用户授权，并返回结果 """
    oauth = None
    oauth_scope = 'snsapi_base' # 'snsapi_base' or 'snsapi_userinfo'

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        self.oauth = WeChatOAuth(app_id=self.wxcfg['app_id'],
                                 secret=self.wxcfg['app_secret'],
                                 redirect_uri=self._get_current_uri(),
                                 scope=self.oauth_scope,
                                 state='ytg')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        # 用户已登录
        if request.user.is_authenticated and cache.get(request.user.username):
            return super().get(request, *args, **kwargs)

        # 用户未登录

        # 授权成功
        code = request.GET.get('code')
        state = request.GET.get('state')
        if code:
            # 获取 access token
            info = self.oauth.fetch_access_token(code)

            # 用户登录
            user, is_created = User.objects.get_or_create(username=info['openid'])
            login(request, user)

            # 保存 refresh token 到当前会话
            request.session['refresh_token'] = info['refresh_token']  # 由于django会话2周内有效，所以不用检查（refresh_token有效期一个月）

            # 缓存 access token
            cache.set(info['openid'], info['access_token'], info['expires_in'])  # 缓存 access token

            return super().get(request, *args, **kwargs)

        # 授权失败
        elif state:
            return HttpResponseForbidden('<h1>微信授权失败！</h1>')

        # 申请授权
        else:
            return HttpResponseRedirect(self.oauth.authorize_url)

    def _get_current_uri(self):
        """返回申请授权的 redirect_url """
        return '{scheme}://{host}{path}'.format(scheme=self.request.scheme,
                                                host=settings.DOMAIN,
                                                path=self.request.path_info)

    @property
    def access_token(self):
        user = self.request.user
        access_token = cache.get(user.username)
        if access_token:
            return access_token

        """
        refresh-token 刷新返回结果示例
        { 
          "access_token":"ACCESS_TOKEN",
          "expires_in":7200,
          "refresh_token":"REFRESH_TOKEN",
          "openid":"OPENID",
          "scope":"SCOPE" 
        }
        """
        refresh_token = self.request.session['refresh_token']
        data = self.oauth.refresh_access_token(refresh_token)
        access_token = data['access_token']
        cache.set(user.username, access_token, data['expires_in'])
        return access_token

    def get_user_info(self):
        return self.oauth.get_user_info(self.request.user.username, self.access_token)

    def create_user(self, request, info):
        # 用户登录
        if self.oauth_scope == 'snsapi_base':
            user, is_created = User.objects.get_or_create(username=info['openid'])
        else:
            user, is_created = User.objects.get_or_create(username=info['openid'])

        login(request, user)


class WxViewContextMixin:
    def get_context_data(self, **kwargs):
        url = '{scheme}://{host}{path}'.format(scheme=self.request.scheme,
                                               host=settings.DOMAIN,
                                               path=self.request.get_full_path())
        timestamp = str(int(time.time()))
        ticket = self.client.jsapi.get_jsapi_ticket()
        nonceStr = 'wechat'
        signature = self.client.jsapi.get_jsapi_signature('wechat', ticket, timestamp, url)
        ctx = super().get_context_data(**kwargs)
        ctx['js_params'] = {
            'appId': self.client.appid,
            'timestamp': timestamp,
            'nonceStr': nonceStr,
            'signature': signature,
        }
        return ctx
