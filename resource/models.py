import os
import random
from django.urls import reverse
from django.conf import settings
from django.db import models
from django.core.cache import cache


class Content(models.Model):
	size = models.PositiveIntegerField(verbose_name='大小')
	hash_val = models.SlugField(max_length=64, verbose_name='哈希值', unique=True)
	hash_type = models.SlugField(max_length=10, default='sha256', verbose_name='哈希类型')
	created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

	class Meta:
		abstract = True
		ordering = ['-created_time', ]


class Resource(Content):
	LINK_TYPE_FILE = 1
	LINK_TYPE_HTTP = 2
	LINK_TYPE_TEXT = 3
	LINK_TYPE = (
		(LINK_TYPE_FILE, '文件'),
		(LINK_TYPE_HTTP, '链接'),
		(LINK_TYPE_TEXT, '文本'),
	)
	STATUS_VERIFY = 0
	STATUS_NORMAL = 1
	STATUS_HIDE = 2
	STATUS = (
		(STATUS_VERIFY, "审核"),
		(STATUS_NORMAL, "正常"),
		(STATUS_HIDE, "隐藏"),
	)
	name = models.CharField(max_length=64, verbose_name='文件名')
	creator = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='创建人')
	link = models.SlugField(max_length=200, verbose_name='链接')
	link_type = models.SmallIntegerField(choices=LINK_TYPE, default=LINK_TYPE_FILE, verbose_name='链接类型')
	type = models.SlugField(max_length=32, verbose_name='文件类型')
	status = models.SmallIntegerField(choices=STATUS, default=STATUS_VERIFY, verbose_name='状态')

	class Meta:
		verbose_name = verbose_name_plural = '资源'

	def __str__(self):
		return self.name

	@classmethod
	def get_download_link(cls, file_id):
		"""获取下载链接"""
		try:
			obj = Resource.objects.get(id=file_id)
		except Resource.DoesNotExist:
			return None

		key = '{}{}'.format(obj.hash_val, random.randint(0, 1e5))
		cache.set(key, obj.link, 86400)  # 24小时有效
		return reverse('resource:download', kwargs={'key': key})

	def delete(self, using=None, keep_parents=False):
		if self.link_type == self.LINK_TYPE_FILE and os.path.exists(self.link):
			os.remove(self.link)
		return super().delete(using=using, keep_parents=keep_parents)


class Material(Content):
	LINK_TYPE_IMG = 1
	LINK_TYPE_VID = 2
	LINK_TYPE_VOC = 3
	LINK_TYPE = (
		(LINK_TYPE_IMG, '图片'),
		(LINK_TYPE_VID, '视频'),
		(LINK_TYPE_VOC, '音频'),
	)
	STATUS_NORMAL = 0
	STATUS_INVISIBLE = 1
	STATUS_DELETE = 2
	STATUS = (
		(STATUS_NORMAL, "正常"),
		(STATUS_INVISIBLE, "不可见"),
		(STATUS_DELETE, "删除"),
	)
	link = models.SlugField(max_length=200, verbose_name='链接')
	link_type = models.SmallIntegerField(choices=LINK_TYPE, verbose_name='链接类型')
	format = models.CharField(max_length=10, verbose_name='格式')
	status = models.SmallIntegerField(choices=STATUS, default=STATUS_INVISIBLE, verbose_name='状态')

	class Meta:
		verbose_name = verbose_name_plural = '物料'

	@classmethod
	def get_link_type(cls, extension):
		if extension in ['jpg', 'jpeg', 'bmp', 'png', 'webp', 'gif', 'tif', 'svg', ]:
			return cls.LINK_TYPE_IMG

	def delete(self, using=None, keep_parents=False):
		filename = os.path.join(settings.RESOURCE_ROOT, os.path.basename(self.link))
		if os.path.exists(filename):
			os.remove(filename)
		return super().delete(using=using, keep_parents=keep_parents)