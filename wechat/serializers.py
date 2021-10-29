import time
import json
from django.conf import settings
from django.urls import reverse
from rest_framework import serializers

from wechatpy.client import WeChatClient
from wechatpy.pay import WeChatPay

from .models import Retail


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
                      trade_body='八鱼樱桃沟', trade_detail='', attach=None, href=None):

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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.params:
            representation.update(self.params)

        return representation


class RetailSerializer(WeChatPayMixin, serializers.ModelSerializer):

    def validate(self, attrs):
        if attrs['total_fee'] <= 0:
            raise serializers.ValidationError('非法的金额')

        return attrs

    def create(self, validated_data):
        instance = super().create(validated_data)
        request = self.context['request']
        username = request.user.username
        self.params = self.create_prepay(validated_data['total_fee'],
                                         notify_url=reverse('wechat:api-retail-result'),
                                         attach=json.dumps({'retail_id': instance.id, 'username': username}))
        return instance

    class Meta:
        model = Retail
        fields = '__all__'
