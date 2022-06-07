import os
from django.contrib import admin
from django.conf import settings
from django.http.response import JsonResponse
from simpleui.admin import AjaxAdmin

from .models import Resource, Material
from .serializers import ResourceSerializer, MaterialSerializer


def get_content_mixin(cls):
	class ContentMixin:
		def size_(self, obj):
			return '{:>6.2f}M'.format(obj.size / 2**20)
		size_.short_description = '大小'

		def change_status(self, request, queryset):
			# 筛选选中的queryset
			ids = request.POST['_selected']
			if not ids:
				return JsonResponse(data={
					'status': 'error',
					'msg': '请先选中数据！'
				})
			queryset.filter(id__in=ids.split(','))

			# 更改状态
			data = request.POST
			queryset.update(status=self.change_status.status[data['status']])
			return JsonResponse({
				'status': 'success',
				'msg': '修改成功！',
			})

		change_status.short_description = '更改状态'
		change_status.type = 'warning'
		change_status.enable = True
		change_status.layer = {
			'params': [{
				'type': 'radio',
				'key': 'status',
				'label': '',
				'options': [{'key': key, 'label': val} for key, val in cls.STATUS],
			}, ]
		}
		change_status.status = {key: val for val, key in cls.STATUS}
	return ContentMixin


@admin.register(Resource)
class ResourceAdmin(get_content_mixin(Resource), AjaxAdmin):
	list_display = 'name type size_ creator status created_time'.split()
	actions = ['upload_file', 'change_status']

	def upload_file(self, request, queryset):
		data = {
			'stream': request.FILES['upload'],
			'link_type': Resource.LINK_TYPE_FILE,
		}
		serializer = ResourceSerializer(data=data, context=dict(request=request))
		if serializer.is_valid():
			serializer.validated_data['status'] = Resource.STATUS_NORMAL
			serializer.save()
			return JsonResponse({
				'status': 'success',
				'msg': '成功上传！',
			})
		else:
			return JsonResponse({
				'status': 'error',
				'msg': serializer.errors,
			})

	upload_file.short_description = '上传'
	upload_file.type = 'success'
	upload_file.icon = 'el-icon-upload'
	upload_file.enable = True
	upload_file.layer = {
		'params': [{
			'type': 'file',
			'key': 'upload',
			'label': '文件',
		}]
	}

	def delete_queryset(self, request, queryset):
		for val in queryset.values('link'):
			filename = val['link']
			if os.path.exists(filename):
				os.remove(filename)
		return super().delete_queryset(request, queryset)


@admin.register(Material)
class MaterialAdmin(get_content_mixin(Material), AjaxAdmin):
	list_display = 'link link_type format size_ status created_time'.split()
	actions = ['upload_file', 'change_status']

	def upload_file(self, request, queryset):
		data = {
			'stream': request.FILES['upload'],
		}
		serializer = MaterialSerializer(data=data, context=dict(request=request))
		if serializer.is_valid():
			serializer.save()
			return JsonResponse({
				'status': 'success',
				'msg': '成功上传！',
			})
		else:
			return JsonResponse({
				'status': 'error',
				'msg': serializer.errors,
			})

	upload_file.short_description = '上传'
	upload_file.type = 'success'
	upload_file.icon = 'el-icon-upload'
	upload_file.enable = True
	upload_file.layer = {
		'params': [{
			'type': 'file',
			'key': 'upload',
			'label': '物料',
		}]
	}

	def delete_queryset(self, request, queryset):
		for val in queryset.values('link'):
			filename = os.path.join(settings.RESOURCE_ROOT, os.path.basename(val['link']))
			if os.path.exists(filename):
				os.remove(filename)
		return super().delete_queryset(request, queryset)
