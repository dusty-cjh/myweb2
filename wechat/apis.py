import uuid
import time
import json
import pytz
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http.response import HttpResponse
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated, BasePermission

from wechatpy.exceptions import InvalidSignatureException

from .mixin import WeChatCommonMixin, WeChatPayResultMixin
from .models import Retail
from .serializers import RetailSerializer


class IsSuperUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class RetailViewSet(ModelViewSet):
    serializer_class = RetailSerializer
    queryset = Retail.objects.all()
    permission_classes = [IsAuthenticated, ]

    def get_permissions(self):
        if self.action == 'destroy' or self.action == 'update':
            self.permission_classes.append(IsSuperUser)

        return [permission() for permission in self.permission_classes]