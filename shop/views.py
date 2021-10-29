import time
from django.views.generic import ListView, TemplateView, DetailView
from django.core.cache import cache
from django.db.models import F
from django.conf import settings

from wechat.mixin import OAuthMixin, WeChatCommonMixin, WxViewContextMixin
from .models import Order, Goods, Appraise


class IndexView(WeChatCommonMixin, WxViewContextMixin, ListView):
	template_name = 'shop/index.html'
	queryset = Goods.objects.filter(status=Goods.STATUS_VISIBLE)


class GoodsDetailView(WeChatCommonMixin, WxViewContextMixin, DetailView):
	template_name = 'shop/detail.html'
	queryset = Goods.objects.filter(status=Goods.STATUS_VISIBLE, nums__gt=0)

	def get(self, request, *args, **kwargs):
		response = super().get(request, *args, **kwargs)
		if 200 <= response.status_code < 300:
			Goods.handle_visit(request, self.object.id)
		return response


class OrderCreateView(OAuthMixin, WxViewContextMixin, DetailView):
	oauth_scope = 'snsapi_userinfo'
	template_name = 'shop/order-create.html'
	queryset = Goods.objects.filter(status=Goods.STATUS_VISIBLE)


class OrderDetailView(OAuthMixin, WxViewContextMixin, DetailView):
	template_name = 'shop/order-detail.html'

	def get_queryset(self):
		return Order.objects.filter(user=self.request.user)


class OrderListView(OAuthMixin, WxViewContextMixin, ListView):
	oauth_scope = 'snsapi_userinfo'
	template_name = 'shop/order-list.html'

	def get_queryset(self):
		qs = Order.objects.filter(user=self.request.user)
		return qs
