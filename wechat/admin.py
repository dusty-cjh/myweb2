import json
from django.contrib import admin
from django.conf import settings
from simpleui.admin import AjaxAdmin
from django.core.cache import caches
from django.urls import reverse
from wechatpy.pay.api import WeChatRefund

from wechat.mixin import WeChatCommonMixin
from .models import Retail, Content, WxAutoReply
from .forms import ContentAdminForm

wxcfg = settings.WECHAT


@admin.register(Content)
class ContentAdmin(AjaxAdmin):
    list_display = ['name', 'content_type', 'content_display']
    list_per_page = 50
    search_fields = ['name', ]
    form = ContentAdminForm

    def content_display(self, obj):
        return obj.content[:20]
    content_display.short_description = '内容'


@admin.register(WxAutoReply)
class WxAutoReply(AjaxAdmin):
    list_display = ['rule', 'keyword', 'content_count', 'reply_type', ]
    list_per_page = 50
    search_fields = ['rule', 'keyword', ]

    def content_count(self, obj):
        return obj.contents.count()
    content_count.short_description = '内容数量'


@admin.register(Retail)
class RetailAdmin(admin.ModelAdmin):
    list_display = ['out_trade_no', 'total_fee_representation', 'status', 'created_time', ]
    fields = ['status', ]
    actions = ['action_refund', ]

    def action_refund(self, request, queryset):
        success_count = 0
        refund = WeChatRefund(client=WeChatCommonMixin.pay)
        for order in queryset:
            if order.out_trade_no:
                refund_fee = order.total_fee
                res = refund.apply(total_fee=refund_fee, refund_fee=refund_fee,
                                   out_trade_no=order.out_trade_no, out_refund_no=order.out_trade_no)
                if res['return_code'] == 'SUCCESS':
                    order.status = Retail.STATUS_REFUNDED
                    order.save()
                    success_count += 1

                    # 向用户发送退款成功通知
                    #
                    #
        self.message_user(request, '申请退款{}笔，成功退款{}笔。'.format(queryset.count(), success_count))
    action_refund.short_description = '批量退款'

    def total_fee_representation(self, obj):
        return str(obj.total_fee / 100)
    total_fee_representation.short_description = '实付款'
