import os
from django.core.cache import cache
from django.db.models import Q
from django.http.response import FileResponse, Http404
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet, GenericViewSet
from rest_framework import mixins
from rest_framework.decorators import action

from .serializers import ResourceSerializer, ResourceDownloadSerializer, MaterialSerializer
from .models import Resource, Material


class IsSuperUser(BasePermission):
	def has_permission(self, request, view):
		return bool(request.user and request.user.is_superuser)


class ResourceViewSet(ModelViewSet):
	serializer_class = ResourceSerializer
	permission_classes = [IsAuthenticated, ]
	queryset = Resource.objects.filter(status=Resource.STATUS_NORMAL)

	def get_permissions(self):
		if self.action == 'destroy':
			self.permission_classes.append(IsAdminUser)
		elif self.action == 'update' or self.action == 'partial_update':
			self.permission_classes.append(IsSuperUser)
		return super().get_permissions()

	def perform_destroy(self, instance):
		if instance.link_type in [Resource.LINK_TYPE_FILE, Resource.LINK_TYPE_TEXT]:
			os.remove(instance.link)
		return super().perform_destroy(instance)

	def retrieve(self, request, *args, **kwargs):
		self.serializer_class = ResourceDownloadSerializer
		instance = self.get_object()
		serializer = self.get_serializer(instance)
		return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

	@action(methods=['GET', ], detail=True)
	def download(self, request, pk=None, format=None):
		try:
			instance = Resource.objects.get(pk=cache.get(pk))
		except Resource.DoesNotExist:
			raise Http404('<h1>数据库中不存在该文件！</h1>')
		except ValueError:
			raise Http404('<h1>业务逻辑错误！</h1>')
		else:
			if not os.path.exists(instance.link):
				raise Http404('<h1>本地文件不存在！</h1>')
			return FileResponse(open(instance.link, 'rb'), filename=Resource.objects.all()[0].link)


class MaterialViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
	serializer_class = MaterialSerializer
	queryset = Material.objects.filter(Q(status=Material.STATUS_NORMAL) | Q(status=Material.STATUS_INVISIBLE))