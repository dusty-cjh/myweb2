from django.contrib import admin
from django.urls import reverse
from django.db.models import Q
from django.utils.html import format_html
from django.http.response import JsonResponse
from django.utils.translation import gettext_lazy as _
from simpleui.admin import AjaxAdmin
from wechatpy.pay.api import WeChatRefund

from wechat.mixin import WeChatCommonMixin
from .models import Goods, Order, Appraise


class GoodsStockFilter(admin.SimpleListFilter):
    title = _("库存")
    parameter_name = "stock"

    def lookups(self, request, model_admin):
        return (
            ('0', _("缺货")),
            ('1', _("有货")),
            ('10', _("库存少于10")),
            ('>=10', _("库存充裕")),
        )

    def queryset(self, request, queryset):
        qs = Goods.objects.all()
        if self.value() == '0':
            return qs.filter(nums=0)
        elif self.value() == '1':
            return qs.filter(nums__gt=0)
        elif self.value() == '10':
            return qs.filter(Q(nums__gt=0) & Q(nums__lt=10))
        elif self.value() == '>=10':
            return qs.filter(nums__gte=10)
        return qs


class GoodsVisibleFilter(admin.SimpleListFilter):
    title = _("首页可见")
    parameter_name = "mainpage_visible"

    def lookups(self, request, model_admin):
        return (
            ('0', _("不可见")),
            ('1', _("可见")),
        )

    def queryset(self, request, queryset):
        qs = Goods.objects.all()
        if self.value() == '0':
            return qs.filter(Q(status=Goods.STATUS_INVISIBLE) | Q(recommend=False) | Q(nums__lte=0))
        elif self.value() == '1':
            return qs.filter(Q(status=Goods.STATUS_VISIBLE) & Q(recommend=True) & Q(nums__gt=0))


@admin.register(Goods)
class GoodsAdmin(AjaxAdmin):
    list_display = 'title link price nums recommend created_time'.split()
    list_filter = (GoodsStockFilter, GoodsVisibleFilter, )
    actions = ['act_recommend', ]
    list_per_page = 30

    def link(self, obj):
        url = reverse("shop:goods", args=(obj.id,))
        return format_html("<a href='{0}'>{0}</a>".format(url))
    link.short_description = '链接'

    def act_recommend(self, request, queryset):
        # 筛选选中的queryset
        data = request.POST
        if not data.get('_selected'):
            return JsonResponse(data={
                'status': 'error',
                'msg': '请先选中数据！'
            })

        # 更改状态
        queryset.update(recommend=int(self.act_recommend.mapping[data['recommend']]))
        return JsonResponse({
            'status': 'success',
            'msg': '修改成功！',
        })

    act_recommend.mapping = {
        '可被推荐': '1',
        '不可推荐': '0',
    }
    act_recommend.short_description = '更改推荐'
    act_recommend.type = 'success'
    act_recommend.enable = True
    act_recommend.layer = {
        'params': [{
            'type': 'radio',
            'key': 'recommend',
            'label': '',
            'options': [{'key': key, 'label': val} for val, key in act_recommend.mapping.items()],
        }, ],
        'confirm_button': '确认提交',
        'cancel_button': '取消',
    }


@admin.register(Appraise)
class AppraiseAdmin(AjaxAdmin):
    list_display = 'order star content created_time'.split()


@admin.register(Order)
class OrderAdmin(AjaxAdmin):
    list_display = 'id out_trade_no user goods nums fee payed_ status created_time'.split()
    actions = 'act_refund'.split()

    def payed_(self, obj):
        return str(round(obj.payed / 100, 2))
    payed_.short_description = '实付款'

    def fee(self, obj):
        return str(round(obj.total_fee / 100, 2))
    fee.short_description = '总价'

    def act_refund(self, request, queryset):
        # check select data
        if len(queryset) == 0:
            return JsonResponse(data={
                'status': 'error',
                'msg': '请先选中数据！'
            })

        # parse request data
        success_count = 0
        refund = WeChatRefund(client=WeChatCommonMixin.pay)
        for order in queryset:
            if order.out_trade_no and order.payed != 0:
                refund_fee = round(order.payed)
                res = refund.apply(total_fee=refund_fee, refund_fee=refund_fee,
                                   out_trade_no=order.out_trade_no, out_refund_no=order.out_trade_no)
                if res['return_code'] == 'SUCCESS':
                    order.payed = 0
                    order.status = Order.STATUS_REFUND
                    order.save()
                    success_count += 1

                    # 向用户发送退款成功通知
                    #
                    #
        self.message_user(request, '申请退款{}笔，成功退款{}笔。'.format(queryset.count(), success_count))

    act_refund.short_description = '退款'
