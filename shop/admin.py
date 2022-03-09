from django.contrib import admin
from django.urls import reverse
from django.db.models import Q
from django.utils.html import format_html
from django.http.response import JsonResponse
from django.utils.translation import gettext as _
from simpleui.admin import AjaxAdmin

from manager import wechat_manager
from .models import Goods, Order, Appraise
from .forms import OrderModelForm, GoodsModelForm


class GoodsStockFilter(admin.SimpleListFilter):
    title = _("Inventory")
    parameter_name = "stock"

    def lookups(self, request, model_admin):
        ret = (
            ('0', _("Stockout")),
            ('1', _("Stock")),
            ('10', _("Stock less than 10")),
            ('>=10', _("Sufficient stock")),
        )
        return ret

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
    title = _("Visible in main page")
    parameter_name = "mainpage_visible"

    def lookups(self, request, model_admin):
        return (
            ('0', _("Invisible")),
            ('1', _("Visible")),
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
    form = GoodsModelForm
    readonly_fields = ('html_preview_image', 'created_time',)
    fieldsets = (
        (_('Edit Info'), {
            'fields': ('title', 'preview', 'html_preview_image', 'fmt', 'content',),
        }),
        (_('Config'), {
            'fields': ('created_time', 'status', 'price', 'nums', 'recommend',),
        }),
        (_('Statistics'), {
            'fields': ('pv', 'uv',),
        }),
    )

    def link(self, obj):
        url = reverse("shop:goods", args=(obj.id,))
        return format_html('<a href="{}"><img src="{}" alt="{}" width="40px;"'.format(url, obj.preview, url))
    link.short_description = _('Link of goods')

    def act_recommend(self, request, queryset):
        # 筛选选中的queryset
        data = request.POST
        if not data.get('_selected'):
            return JsonResponse(data={
                'status': 'error',
                'msg': _('Please pick on first')
            })

        # 更改状态
        queryset.update(recommend=int(self.act_recommend.mapping[data['recommend']]))
        return JsonResponse({
            'status': 'success',
            'msg': _('Updated'),
        })

    act_recommend.mapping = {
        _('Recommended'): '1',
        _('Unrecommended'): '0',
    }
    act_recommend.short_description = _('Change recommend strategy')
    act_recommend.type = 'success'
    act_recommend.enable = True
    act_recommend.layer = {
        'params': [{
            'type': 'radio',
            'key': 'recommend',
            'label': '',
            'options': [{'key': key, 'label': val} for val, key in act_recommend.mapping.items()],
        }, ],
        'confirm_button': _('Confirm to submit'),
        'cancel_button': _('Cancel'),
    }


@admin.register(Appraise)
class AppraiseAdmin(AjaxAdmin):
    list_display = 'order star content created_time'.split()


@admin.register(Order)
class OrderAdmin(AjaxAdmin):
    list_display = 'id out_trade_no user goods nums fee payed_ status created_time'.split()
    form = OrderModelForm
    actions = 'act_refund act_redpack'.split()

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
                'msg': _('Please pitch on items first')
            })

        # parse request data
        success_count = 0
        for order in queryset:
            if order.out_trade_no and order.payed != 0:
                refund_fee = round(order.payed)
                res = wechat_manager.wechatpay_refund(refund_fee, order.out_trade_no)
                request.log.info('shop.OrderAdmin.act_refund|{}', res)
                if res.return_code == 'SUCCESS':
                    order.payed = 0
                    order.status = Order.STATUS_REFUND
                    order.save()
                    success_count += 1

                    # send notification of success refunding for user
                    #
                    #
        self.message_user(request, _('applied for {} refunds, permitted {} refunds').format(queryset.count(), success_count)),
    act_refund.short_description = _('Refund')

    def act_redpack(self, request, queryset):
        # check select data
        if len(queryset) == 0:
            return JsonResponse(data={
                'status': 'error',
                'msg': _('Please pitch on items first')
            })

        resp = wechat_manager.wechatpay_redpack(queryset[0].user.username, 10)
        request.log.info('shop.OrderAdmin.act_redpack|{}', resp)
        self.message_user(request, _('Sended red packet success'))
    act_redpack.short_description = _('Send redpack')
