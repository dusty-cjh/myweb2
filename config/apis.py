import os
import glob
import shutil
from django.http.response import Http404
from rest_framework.viewsets import GenericViewSet, ViewSet, ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins

from .models import Material
from .serializers import MaterialSerializer


class MaterialViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      GenericViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = MaterialSerializer
    queryset = Material.all()
    lookup_value_regex = '.*'

    def get_object(self):
        pk = self.kwargs['pk']
        try:
            instance = Material(pk)
        except FileNotFoundError:
            raise Http404('文件{}不存在'.format(pk))

        return instance

    def list(self, request, *args, **kwargs):

        return super().list(request, *args, **kwargs)
