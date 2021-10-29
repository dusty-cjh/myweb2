from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Post, Summary
from .forms import PostAdminForm


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

