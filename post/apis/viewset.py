import abc
import functools
from django.core.cache import cache
from django.db.models import F
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from post.serializers import SummarySerializer, PostSerializer
from post.models import Summary, Post, PostBase
from post.filters import SummaryFilter
from logging import getLogger

log = getLogger('statistic')


class QuerySet:
    def __get__(self, instance, owner):
        import sys
        cls = getattr(sys.modules[__name__], owner.__name__[:-7])
        if not cls:
            raise ValueError('请导入正确的实例对象，如：from xxx import {}'.format(owner[:-7]))
        else:
            return self.get_queryset(cls)

    @abc.abstractmethod
    def get_queryset(self, cls):
        """重写这个函数，以返回正确的queryset"""
        return cls.objects.all()


class QuerySetVisible(QuerySet):
    def get_queryset(self, cls):
        return cls.objects.filter(status=cls.STATUS_VISIBLE)


class SummaryViewSet(ReadOnlyModelViewSet):
    serializer_class = SummarySerializer
    filter_class = SummaryFilter

    def get_queryset(self):
        handle = 'get_' + self.request.GET.get('category', '')
        if hasattr(Summary, handle):
            qs = getattr(Summary, handle)()
        else:
            qs = Summary.objects.all()

        return qs

    @action(methods=['patch'], detail=True)
    def visit_count(self, request, pk=None):
        """
        文章访问计数

        pv: Page View       点击量（该网页被请求了多少次）
        uv: Unique Visitor  访问量（有多少用户访问了该网页）
        """
        increase_pv = False
        increase_uv = False

        uid = self.request.uid
        pv_key = 'pv:{}:{}'.format(uid, self.request.path)
        uv_key = 'uv:{}:{}'.format(uid, self.request.path)

        if not cache.get(pv_key):
            increase_pv = True
            cache.set(pv_key, 1, 1*60)  # 1min 有效

        if not cache.get(uv_key):
            increase_uv = True
            cache.set(uv_key, 1, 24 * 60 * 60)

        if increase_uv and increase_pv:
            Summary.objects.filter(pk=pk).update(pv=F('pv')+1, uv=F('uv')+1)
        elif increase_pv:
            Summary.objects.filter(pk=pk).update(pv=F('pv')+1)
        elif increase_uv:
            Summary.objects.filter(pk=pk).update(uv=F('uv')+1)

        return Response({
            'type': 'echo',
            'value': 'OK',
        }, status=status.HTTP_202_ACCEPTED)


class PostViewSet(ReadOnlyModelViewSet):
    queryset = QuerySetVisible()
    serializer_class = PostSerializer
