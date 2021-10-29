import json
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.db.models import Q, F
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission, IsAdminUser

from wechat.apis import WeChatPayResultMixin
from .serializers import GoodsSerializer, OrderSerializer, AppraiseSerializer
from .models import Goods, Order, Appraise


class IsOrderOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class GoodsViewSet(ReadOnlyModelViewSet):
    queryset = Goods.latests()
    serializer_class = GoodsSerializer

    @action(methods=['patch'], detail=True)
    def visit_count(self, request, pk=None):
        """
        文章访问计数

        pv: Page View       点击量（该网页被请求了多少次）
        uv: Unique Visitor  访问量（有多少用户访问了该网页）
        """
        Goods.handle_visit(request, pk)

        return Response({
            'type': 'echo',
            'value': 'OK',
        }, status=status.HTTP_202_ACCEPTED)

    def get_permissions(self):
        if not self.action in ['list', 'retrieve', 'visit_count']:
            self.permission_classes.append(IsAdminUser)
        return super().get_permissions()


class AppraiseViewSet(ModelViewSet):
    queryset = Appraise.objects.all()
    serializer_class = AppraiseSerializer


class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        if 'refund_reason' in request.data:
            request.data['status'] = Order.STATUS_REFUND
        return super().partial_update(request, *args, **kwargs)


class OrderCreateCallbackAPI(WeChatPayResultMixin, APIView):
    def pay_valid(self, result):
        # 对该订单号进行处理
        order_id = int(result['attach'])
        Order.objects.filter(id=order_id).update(status=Order.STATUS_DEALING,
                                                              total_fee=result['cash_fee'],
                                                              out_trade_no=result['out_trade_no'],
                                                              payed=result['cash_fee'],)
        order = Order.objects.get(id=order_id)
        Goods.objects.filter(id=order.goods.id).update(nums=F('nums')-1)
        # 向用户发送通知
        self.template_reply(order.user.username, order)

    def pay_invalid(self, result):
        # 对该订单号进行处理
        pass

    def template_reply(self, username, order):
        template_id = 'WfBl0WZj_XIUkV1nKKavI9n34d-5CnhFg6PlcdjOD5o'
        url = settings.DOMAIN + reverse('shop:order-detail', args=(order.id,))
        addr = json.loads(order.address)
        data = {
            'first': {
                'value': '🍒下单成功！',
            },
            'keyword1': {
                'value': '{:.2f}'.format(order.payed / 100),
            },
            'keyword2': {
                'value': '在线支付',
            },
            'keyword3': {
                'value': order.goods.title,
                'color': '#ff0000',
            },
            'keyword4': {
                'value': '{}{}{}'.format(addr['userName'], addr['telNumber'],
                                         addr['provinceName']+addr['cityName']+addr['countryName']+
                                         addr['detailInfo']),
            },
            'keyword5': {
                'value': str(order.id),
            },
            'remark': {
                'value': '点击查看详情',
            },
        }
        result = self.client.message.send_template(username, template_id, data, url=url)
        pass
