import time, markdown, json
import logging
from django.views.generic import ListView, TemplateView, DetailView, View
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.db.models import F
from django.conf import settings
from django.http import JsonResponse, HttpRequest

from manager.utils import json_error_response, parse_data_from_markdown, json_response, yaml_response, yaml_error_response
from manager import wechat_manager
from wechat.mixin import OAuthMixin, WeChatCommonMixin, WxViewContextMixin
from .models import Order, Goods, Appraise

log = logging.getLogger('info')


class IndexView(WeChatCommonMixin, WxViewContextMixin, ListView):
	template_name = 'shop/index.html'
	queryset = Goods.objects.filter(status=Goods.STATUS_VISIBLE)

	def get(self, request, *args, **kwargs):
		request.log.data('view|shop-index')
		return super().get(request, *args, **kwargs)


class GoodsDetailView(WeChatCommonMixin, WxViewContextMixin, DetailView):
	template_name = 'shop/detail.html'
	queryset = Goods.objects.filter(status=Goods.STATUS_VISIBLE, nums__gt=0)

	def get_object(self, queryset=None):
		obj = super().get_object(queryset)
		if obj.fmt == 'markdown':
			exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite', 'markdown.extensions.tables',
					'markdown.extensions.toc']
			obj.content = markdown.markdown(obj.content, extensions=exts)

		return obj

	def get(self, request, *args, **kwargs):
		request.log.data('view|goods-detail')
		response = super().get(request, *args, **kwargs)
		if 200 <= response.status_code < 300:
			Goods.handle_visit(request, self.object.id)
		return response


class OrderCreateView(OAuthMixin, WxViewContextMixin, DetailView):
	oauth_scope = 'snsapi_userinfo'
	template_name = 'shop/order-create.html'
	queryset = Goods.objects.filter(status=Goods.STATUS_VISIBLE)

	def get_address(self):
		addr = self.request.session.get('user_address', None)
		if addr is None:
			order = Order.objects.filter(user=self.request.user).order_by('-created_time').first()
			log.info('get-user-order:{}'.format(order))
			if order is not None:
				try:
					addr = json.loads(order.address)
				except Exception as e:
					log.warning('shop/order-create.html|get user address failed, error={}'.format(repr(e)))
				else:
					self.request.session['user_address'] = addr
		return addr

	def get_context_data(self, **kwargs):
		self.request.log.data('view|order-create')
		ctx = super().get_context_data(**kwargs)
		ctx['address'] = self.get_address()
		log.info('context|{}'.format(ctx))
		return ctx


class OrderDetailView(OAuthMixin, WxViewContextMixin, DetailView):
	template_name = 'shop/order-detail.html'

	def get_queryset(self):
		self.request.log.data('view|order-detail')
		return Order.objects.filter(user=self.request.user)


class OrderListView(OAuthMixin, WxViewContextMixin, ListView):
	oauth_scope = 'snsapi_userinfo'
	template_name = 'shop/order-list.html'

	def get_queryset(self):
		self.request.log.data('view|order-list')
		qs = Order.objects.filter(user=self.request.user)
		return qs


class CreateGoodsView(View):
	@csrf_exempt
	def dispatch(self, request, *args, **kwargs):
		return super().dispatch(request, *args, **kwargs)

	def has_permission(self):
		if self.request.user.is_staff:
			return True

		key = settings.WECHAT['aes_key']
		if self.request.headers['myweb2-secret'] == key:
			return True

	def post(self, request: HttpRequest):
		# validate
		if not self.has_permission():
			return json_error_response('has no permission')

		# receive file
		files = list(request.FILES.values())
		if len(files) == 0:
			return json_error_response('param validation error')
		else:
			fp = files[0]
		#
		content, metadata = parse_data_from_markdown(str(fp.read(), encoding='utf8'))

		# update goods
		id = metadata.pop('id') or metadata.pop('pk')
		if id:
			return self.update_goods(id, content, metadata)
		else:
			return self.create_goods(content, metadata)

	def response(self, obj, status):
		fmt = self.request.GET.get('fmt', 'json')
		if fmt == 'yaml':
			return yaml_response(obj, status)
		else:
			return json_response(obj, status)

	def create_goods(self, content, metadata):
		try:
			obj, ok = Goods.objects.get_or_create(content=content, **metadata)
		except Exception as e:
			log.error('CreateGoodsView|error={}'.format(repr(e)))
			return json_error_response(e, 500)
		status = 201 if ok else 200
		return self.response(obj, status)

	def update_goods(self, id, content, metadata):
		try:
			count = Goods.objects.filter(id=id).update(content=content, **metadata)
		except Exception as e:
			log.error('CreateGoodsView|update_goods|error={}'.format(repr(e)))
			return json_error_response(e, 500)
		return self.response(dict(updated=count), 200)
