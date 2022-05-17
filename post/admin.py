from datetime import timedelta
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _
from common import utils
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
    fields = 'title content content_type author status'.split()
    form = ArticleAdminForm

    def link(self, obj):
        url = reverse("post:article", args=(obj.id,))
        return format_html("<a href='{0}'>{0}</a>".format(url))
    link.short_description = 'Hyperlink'


@admin.register(AsyncFuncJob)
class AsyncFuncJobAdmin(admin.ModelAdmin):
    list_display = 'id func_name job_type params status col_retry expire_time mtime ctime result'.split()
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
    actions = ['act_copy']

    def save_model(self, request, obj: AsyncFuncJob, form, change):
        now = utils.get_datetime_now()
        if not obj.mtime:
            obj.mtime = now
        if not obj.expire_time:
            obj.expire_time = obj.mtime + timedelta(seconds=obj.max_lifetime)
        if not obj.result:
            obj.result = ''

        return super().save_model(request, obj, form, change)

    def act_copy(self, request, queryset):
        success_count = 0
        for obj in queryset:
            obj.pk = None
            try:
                obj.save()
            except Exception as e:
                pass
            else:
                success_count += 1
        self.message_user(request, _(f'copied {success_count}/{len(queryset)} rows'))
    act_copy.short_description = 'copy rows'

    def col_retry(self, obj: AsyncFuncJob):
        return f'{obj.retries}/{obj.max_retry}'
    col_retry.short_description = 'Tries'
