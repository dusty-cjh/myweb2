import os
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import render
from wechatpy.pay.api import WeChatRefund
from django_pandas.io import read_frame
from django.conf import settings
from django.http.response import HttpResponseRedirect, FileResponse, Http404
from simpleui.admin import AjaxAdmin

from wechat.mixin import WeChatCommonMixin
from .models import StudyCollect, VersionConfig, PresentCollect


@admin.register(StudyCollect)
class StudyCollectAdmin(AjaxAdmin):
    list_display = ['name', 'version', 'sex', 'age', 'school', 'phone', 'payed_fee', 'status', 'created_time']
    fields = ['name', 'sex', 'age', 'school', 'phone', 'ps', 'out_trade_no', 'cash_fee', 'owner', 'version', 'status',]
    actions = ['action_refund', 'action_export']
    list_filter = ['version', 'status', 'created_time', ]

    def action_refund(self, request, queryset):
        success_count = 0
        refund = WeChatRefund(client=WeChatCommonMixin.pay)
        for order in queryset:
            if order.out_trade_no:
                refund_fee = int(order.cash_fee)
                res = refund.apply(total_fee=refund_fee, refund_fee=refund_fee,
                                   out_trade_no=order.out_trade_no, out_refund_no=order.out_trade_no)
                if res['return_code'] == 'SUCCESS':
                    order.status = StudyCollect.STATUS_REFUND
                    order.save()
                    success_count += 1

                    # 向用户发送退款成功通知
                    #
                    #
        self.message_user(request, '申请退款{}笔，成功退款{}笔。'.format(queryset.count(), success_count))
    action_refund.short_description = '批量退款'

    def action_export(self, request, queryset):
        df = read_frame(queryset)
        df.created_time = df.created_time.apply(lambda x: x.strftime('%Y-%m-%d %H:%M'))
        df.to_excel(os.path.join(settings.MEDIA_ROOT, '学员信息.xlsx'))
        return HttpResponseRedirect(f'{settings.MEDIA_URL}学员信息.xlsx')
    action_export.short_description = '导出为excel'

    def payed_fee(self, obj):
        return obj.cash_fee / 100
    payed_fee.short_description = '支付金额'


@admin.register(VersionConfig)
class VersionConfigAdmin(AjaxAdmin):
    list_display = 'version signup_url fee created_time'.split()
    fields = ['version', 'fee', 'url', 'img', ]

    def signup_url(self, obj):
        return format_html('<a href="{url}" target="_blank" >点击访问</a>'
                           .format(url=reverse('collect:sign-up', args=(obj.version,))))
    signup_url.short_description = '用户访问链接'


@admin.register(PresentCollect)
class PresentCollect(AjaxAdmin):
    list_display = ['contact', 'user', 'title', 'price', 'name', 'addr', 'created_time', ]
    actions = ['action_export', 'action_download']

    def action_export(self, request, queryset):
        df = read_frame(queryset)
        df.created_time = df.created_time.apply(lambda x: x.strftime('%Y-%m-%d %H:%M'))
        for i, previews in enumerate(df.previews):
            df.previews[i] = ';'.join([WeChatCommonMixin.client.media.get_url(media_id)
                                        for media_id in previews.split(';')[:-1]])
        df.to_excel(filename := os.path.join(settings.MEDIA_ROOT, '物品信息.xlsx'))
        return FileResponse(open(filename, 'rb'), filename='物品信息.xlsx')
    action_export.short_description = '导出为excel'

    def action_download(self, request, queryset):
        if not request.user.is_staff:
            raise Http404('page not found')

        # 获取物品的下载链接
        for obj in queryset:
            obj.previews_url = [WeChatCommonMixin.client.media.get_url(media_id)
                                for media_id in obj.previews.split(';')[:-1]]

        ctx = {
            'object_list': queryset,
        }
        response = render(request, 'collect/present_download.html', ctx, 'text/html', 200)
        return response
    action_download.short_description = '通过网页下载素材'
