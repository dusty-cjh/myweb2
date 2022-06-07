import json
import pytz
from django.utils.decorators import method_decorator
from django.contrib.auth import settings, login
from django.contrib.auth.models import User
from django.views.generic import View, TemplateView
from django.http.response import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from wechatpy.replies import create_reply, TextReply, EmptyReply, ImageReply, TransferCustomerServiceReply
from wechatpy.messages import TextMessage, BaseField
from wechatpy.events import SubscribeEvent
from wechatpy.oauth import WeChatOAuth

from manager import wechat_manager
from .mixin import OAuthMixin, WeChatPayResultMixin
from .models import Retail, WxAutoReply
from .decorators import check_signature


class RetailView(OAuthMixin, TemplateView):
    template_name = 'wechat/retail.html'


class MobileView(TemplateView):
    template_name = 'wechat/mobile.html'


class RetailPayResultAPI(WeChatPayResultMixin, View):

    def pay_valid(self, result):
        out_trade_no = result['out_trade_no']
        attach = json.loads(result['attach'])
        retail_id, username = attach['retail_id'], attach['username']

        # 更新零售订单信息
        retail = Retail.objects.get(id=retail_id)
        retail.status = Retail.STATUS_PAYED
        retail.out_trade_no = out_trade_no
        retail.save()

        # 在微信中通知用户支付结果
        # self.text_reply(retail, username)
        self.template_reply(retail, username)

    def template_reply(self, retail, username):
        template_id = 'GoRtiHVaqM98oWvNOOYRn5-Tynr_sXnggOTpNB1f8dQ'
        data = {
            'pay': {
                'value': '{:.2f}'.format(retail.total_fee / 100),
                'color': '#fbcb00',
            },
            'address': {
                'value': '八鱼樱桃沟零售',
                'color': '#55d500',
            },
            'time': {
                'value': retail.created_time.astimezone(tz=pytz.timezone(settings.TIME_ZONE)).strftime(
                    '%Y-%m-%d %H:%M'),
                'color': '#55d500',
            },
            'remark': {
                'value': '如有疑问，请咨询137 8035 9572',
                'color': '#005aff',
            },
        }
        result = self.client.message.send_template(username, template_id,
                                                   data=data,
                                                   url='http://{}/wechat/retail/'.format(settings.DOMAIN))
        pass

    def text_reply(self, retail, username):
        SUCCESS_REPLY = """🍒🍒您已成功支付{total_fee:.2f}元\r\n\r\n类型：零售扫码\r\n时间：{created_time}"""
        created_time = retail.created_time.astimezone(tz=pytz.timezone(settings.TIME_ZONE)).strftime('%Y-%m-%d %H:%M')
        self.client.message.send_text(username,
                                      SUCCESS_REPLY.format(total_fee=retail.total_fee / 100, created_time=created_time))


class OAuthView(View):
    """
    必须在微信中打开，自动获取用户信息并通过cookies建立会话
    """
    SCOPE = 'snsapi_userinfo'

    def dispatch(self, request, *args, **kwargs):
        # 用户已登录且access_token未到期
        if request.user.is_authenticated:
            return super().dispatch(request, *args, *kwargs)

        # access_token已到期，重新获取
        else:
            oauth = WeChatOAuth(settings.WECHAT['app_id'],
                                settings.WECHAT['app_secret'],
                                settings.DOMAIN + request.path,
                                scope=self.SCOPE)
            code = request.GET.get('code', None)

            if code is None:
                return HttpResponseRedirect(oauth.authorize_url)
            else:
                access_token = oauth.fetch_access_token(code)
                info = oauth.get_user_info()

                user, is_created = User.objects.update_or_create(username=info['nickname'],
                                                                 openid=info['openid'],
                                                                 unionid=info['unionid'],
                                                                 sex=info['sex'],
                                                                 city=info['city'],
                                                                 province=info['province'],
                                                                 headimgurl=info['headimgurl'])
                login(request, user)
            return super().dispatch(request, *args, **kwargs)


@method_decorator(csrf_exempt, name='dispatch')
class IndexView(TemplateView):
    template_name = 'wechat/index.html'

    @check_signature
    def get(self, request, *args, **kwargs):
        return HttpResponse('hello world')

    @check_signature
    def post(self, request, *args, **kwargs):
        # parse wechat message
        reply = EmptyReply()
        msg = wechat_manager.parse_wechat_message(request)
        log_data = ['{}={}'.format(k, getattr(msg, k, ''))
                                   for k in msg._fields.keys()
                                   if hasattr(msg, k)]
        request.log.data(
            'wechat_message|request|{}|'.format(msg.__class__.__name__)
            + '|'.join(log_data)
        )  # parse data to csv file by keyword

        # handle message
        handle = getattr(self, msg.type, None)
        if handle:
            content = handle(msg) or reply
            request.log.data(
                'wechat_message|response|{}|'.format(content.__class__.__name__) +
                '|'.join(['{}={}'.format(k, getattr(content, k, ''))
                 for k in content._fields.keys()
                 if hasattr(content, k)]),
            )
            return HttpResponse(content=content or reply, status=200)
        else:
            return HttpResponse('不支持的消息类型', status=400)

    def text(self, msg: TextMessage):
        if msg.content == '人工':
            return self.kf(self.request, msg)
        try:
            obj = WxAutoReply.objects.get(keyword=msg.content)
        except WxAutoReply.DoesNotExist:
            return EmptyReply().render()
        # 回复第一条信息
        reply = obj.contents.all()[0]
        return reply.get_reply(msg).render()

    def kf(self, request, msg):
        reply = TransferCustomerServiceReply(message=msg)
        return reply.render()

    def event(self, msg: SubscribeEvent):
        handle = getattr(self, 'event_%s' % msg.event, None)
        if handle:
            return handle(msg)
        else:
            self.request.log.warning('unprocessed_message={}', msg)

    def event_subscribe(self, event):
        text = """♥感谢您的关注~"""

        return create_reply(text, event)
