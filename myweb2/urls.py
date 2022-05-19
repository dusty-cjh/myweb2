"""myweb2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', include('post.urls')),
    path('collect/', include('collect.urls')),
    path('wechat/', include('wechat.urls')),
    path('admin/', admin.site.urls),
    path('shop/', include('shop.urls')),
    path('resource/', include('resource.urls')),
    path('mybot/', include('mybot.urls')),
    path('pages/', include('django.contrib.flatpages.urls')),

    path('ckeditor/', include('ckeditor_uploader.urls')),
] \
              + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls
from post.apis import SummaryViewSet, PostViewSet
from collect.apis import StudyCollectViewSet
from wechat.apis import RetailViewSet
from resource.apis import ResourceViewSet
from resource.apis import MaterialViewSet
from shop.apis import GoodsViewSet, OrderViewSet, AppraiseViewSet

router = DefaultRouter()
router.register('summary', SummaryViewSet, 'summary')
router.register('goods', GoodsViewSet, 'goods')
router.register('post', PostViewSet, 'post')
router.register('collect-study', StudyCollectViewSet, 'collect-study')
router.register('retail', RetailViewSet, 'retail')
router.register('resource', ResourceViewSet, 'resource')
router.register('material', MaterialViewSet, 'material')
router.register('order', OrderViewSet, 'order')
router.register('appraise', AppraiseViewSet, 'appraise')

urlpatterns += [
    path('api/', include(router.urls)),
    path('api/doc/', include_docs_urls(title='API Doc')),
]
