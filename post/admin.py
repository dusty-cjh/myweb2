from django.contrib import admin

from .models import Post, Summary, Goods
from .forms import PostAdminForm


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = 'title status created_time'.split()
    fields = 'title content status '.split()
    form = PostAdminForm


@admin.register(Goods)
class GoodsAdmin(admin.ModelAdmin):
    list_display = 'title price sales visit status created_time'.split()
    fields = 'title content price sales visit status '.split()


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = 'title type recommend mainpage created_time'.split()
    fields = 'title desc url type recommend mainpage preview'.split()

