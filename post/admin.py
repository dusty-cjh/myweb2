import time
from datetime import timedelta
from django.db import transaction
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _
from common import utils
from . import managers
from .models import Post, Summary, Article, AsyncFuncJob
from .forms import ArticleAdminForm


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = 'title link status created_time'.split()
    fields = 'title content status '.split()
    # form = PostAdminForm

    def link(self, obj):
        url = reverse("post:post", args=(obj.id,))
        return format_html("<a href='{0}'>{0}</a>".format(url))
    link.short_description = '链接'

    def get_urls(self):
        urls = super().get_urls()

        #   通过更新 /add/ 链接可以把urls换掉

        return urls


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = 'title type recommend mainpage created_time'.split()
    fields = 'title desc url type recommend mainpage preview'.split()


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = 'title link author status created_time'.split()
    list_display_links = 'title'.split()
    list_editable = 'status'.split()
    list_per_page = 10
    list_max_show_all = 200
    list_select_related = 'author'.split()
    fields = 'title content content_type author status'.split()
    form = ArticleAdminForm
    search_fields = 'title'.split()
    date_hierarchy = 'created_time'
    list_filter = 'status author__is_superuser'.split()

    def link(self, obj):
        url = reverse("post:article", args=(obj.id,))
        return format_html("<a href='{0}'>{0}</a>".format(url))
    link.short_description = 'Hyperlink'

    def save_form(self, request, form, change):
        # add default value
        obj = super().save_form(request, form, change)
        obj.author = request.user
        return obj

    def save_model(self, request, obj, form, change):
        # run in transaction
        with transaction.atomic():
            ret = super().save_model(request, obj, form, change)

            # auto add summary
            if not change:
                managers.create_summary_from_article(obj)
                pass

            return ret

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(author=request.user)


@admin.register(AsyncFuncJob)
class AsyncFuncJobAdmin(admin.ModelAdmin):
    list_display = 'id col_func_name job_type params status col_retry expire_time result'.split()
    list_editable = 'status'.split()
    list_per_page = 10
    list_max_show_all = 200
    search_fields = 'func_name status'.split()
    list_filter = 'status'.split()
    fieldsets = (
        (_('Job Parameters'), {
            'fields': ('func_name', 'job_type', 'params', ),
        }),
        (_('Job Config'), {
            'fields': ('max_retry', 'max_lifetime', 'expire_time', ),
        }),
        (_('Advance Settings'), {
            'fields': ('status', 'retries', 'result', 'mtime'),
        }),
    )
    actions = ['act_copy', 'act_to_pending', 'act_to_success', 'act_to_pause', ]

    def save_model(self, request, obj: AsyncFuncJob, form, change):
        now = utils.get_datetime_now()
        if not obj.mtime:
            obj.mtime = now
        if not obj.expire_time:
            obj.expire_time = obj.mtime + timedelta(seconds=obj.max_lifetime)
        if not obj.result:
            obj.result = ''

        return super().save_model(request, obj, form, change)

    def act_copy(self, request, queryset: list[AsyncFuncJob]):
        success_count = 0
        for obj in queryset:
            obj.pk = None
            obj.result = ''
            obj.set_params(obj.parse_params())  # parameters formatter
            obj.ctime = obj.mtime = obj.expire_time = utils.get_datetime_now()
            try:
                obj.save()
            except Exception as e:
                pass
            else:
                success_count += 1
        self.message_user(request, _(f'copied {success_count}/{len(queryset)} rows'))
    act_copy.short_description = _('copy rows')

    def act_to_pending(self, request, queryset):
        affected = queryset.update(status=AsyncFuncJob.STATUS_PENDING, retries=0)
        self.message_user(request, _(f'{affected}/{len(queryset)} has to pending'))
    act_to_pending.short_description = _('To pending')

    def act_to_success(self, request, queryset):
        affected = queryset.update(status=AsyncFuncJob.STATUS_SUCCESS)
        self.message_user(request, _(f'{affected}/{len(queryset)} has to success'))
    act_to_success.short_description = _('To success')

    def act_to_pause(self, request, queryset):
        affected = queryset.update(status=AsyncFuncJob.STATUS_PAUSE)
        self.message_user(request, _(f'{affected}/{len(queryset)} has to pause'))
    act_to_pause.short_description = _('To pause')

    def col_retry(self, obj: AsyncFuncJob):
        return f'{obj.retries}/{obj.max_retry}'
    col_retry.short_description = _('Tries')

    def col_func_name(self, obj: AsyncFuncJob):
        return obj.func_name.split('-')[-1]
    col_func_name.short_description = _('Task Name')

