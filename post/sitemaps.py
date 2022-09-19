from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from .models import Article

info_dict = {
    'queryset': Article.objects.filter(status=Article.STATUS_VISIBLE),
    'date_field': 'pub_date',
}

urlpatterns = [
    # some generic view using info_dict
    # ...

    # the sitemap
    path('sitemap.xml', sitemap,
         {'sitemaps': {'blog': GenericSitemap(info_dict, priority=0.6)}},
         name='django.contrib.sitemaps.views.sitemap'),
]
