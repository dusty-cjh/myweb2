import functools
from django.contrib.auth import settings, login
from django.contrib.auth.models import User
from django.http.response import HttpResponseBadRequest, HttpResponse, HttpResponseRedirect, FileResponse, Http404
from wechatpy.utils import check_signature as wechatpy_check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.oauth import WeChatOAuth
from wechatpy import parse_message
from wechatpy.replies import EmptyReply, TransferCustomerServiceReply


def check_signature(func):
	"""
	检查请求有效性，若为接口验证则返回echostr
	"""
	@functools.wraps(func)
	def get(self, request, *args, **kwargs):
		try:
			wechatpy_check_signature(settings.WECHAT['token'],
									 request.GET.get('signature'),
									 request.GET.get('timestamp'),
									 request.GET.get('nonce'))
		except InvalidSignatureException:
			return HttpResponseBadRequest('<h1>不合法的请求签名</h1><p>此页面仅为微信提供，非微信官网不可访问</p>')

		# 是否为验证请求
		echostr = request.GET.get('echostr')
		if echostr:
			return HttpResponse(echostr)
		else:
			return func(self, request, *args, **kwargs)
	return get


def oauth(scope='snsapi_userinfo'):
	"""
	网页授权装饰器，一般放在view的get方法上就行
	"""
	def decorator(func):
		@functools.wraps(func)
		def wrapper(self, request, *args, **kwargs):
			# 用户已登录且access_token未到期
			if request.user.is_authenticated:
				return func(self, request, *args, **kwargs)

			# access_token已到期，重新获取
			else:
				oauth = WeChatOAuth(settings.WECHAT['appid'],
									settings.WECHAT['secret'],
									settings.DOMAIN + request.path,
									scope=self.SCOPE)
				code = request.GET.get('code', None)

				if code is None:
					return HttpResponseRedirect(oauth.authorize_url)
				else:
					access_token = oauth.fetch_access_token(code)
					info = oauth.get_user_info()

					user, is_created = User.objects.get_or_create(username=info['nickname'],
																		 openid=info['openid'],
																		 unionid=info['unionid'],
																		 sex=info['sex'],
																		 city=info['city'],
																		 province=info['province'],
																		 headimgurl=info['headimgurl'])
					login(request, user)
			return func(self, request, *args, **kwargs)
		return wrapper
	return decorator
