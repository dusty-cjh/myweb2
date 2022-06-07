# import os
# import random
# from hashlib import sha256
# from django.conf import settings
# from django.contrib.auth.models import User
# from django.core.cache import cache
# from django.urls import reverse
# from rest_framework import serializers
#
# from .models import Resource, Material, Content
#
#
# if not os.path.exists(settings.RESOURCE_ROOT):
# 	os.mkdir(settings.RESOURCE_ROOT)
#
#
# class ResourceSerializer(serializers.Serializer):
# 	TMP_FILE = os.path.join(settings.RESOURCE_ROOT, 'tmp')
#
# 	# upload
# 	stream = serializers.FileField(write_only=True)
# 	hash_val = serializers.SlugField(required=False)
# 	hash_type = serializers.SlugField(required=False)
# 	link_type = serializers.ChoiceField(choices=Resource.LINK_TYPE, required=True)
# 	# read
# 	id = serializers.IntegerField(read_only=True)
# 	name = serializers.CharField(max_length=64, read_only=True)
# 	size = serializers.IntegerField(read_only=True)
# 	type = serializers.CharField(max_length=20, read_only=True)
# 	creator = serializers.PrimaryKeyRelatedField(read_only=True)
# 	created_time = serializers.DateTimeField(read_only=True)
#
# 	def create(self, validated_data):
# 		# parse
# 		stream, link_type = validated_data.pop('stream'), validated_data.pop('link_type')
# 		hash_val, hash_type = validated_data.pop('hash_val', None), validated_data.pop('hash_type', None)
#
# 		# create unique file link
# 		filename = '{}{}'.format(random.randint(1e4, 1e5 - 1), stream.name)
# 		file = Resource(name=filename, size=stream.size, type=stream.content_type,
# 						link=os.path.join(settings.RESOURCE_ROOT, filename), link_type=link_type)
#
# 		# save file and calc hash value
# 		if hash_val and hash_type == 'sha256':
# 			try:
# 				f = Resource.objects.get(hash_val)
# 			except Resource.DoesNotExist:
# 				with open(file.link, 'wb') as fp:
# 					for chunk in stream.chunks(4096):
# 						fp.write(chunk)
# 			else:
# 				return f
# 		else:
# 			h, hash_type = sha256(), 'sha256'
# 			with open(file.link, 'wb') as fp:
# 				for chunk in stream.chunks(4096):
# 					h.update(chunk)
# 					fp.write(chunk)
#
# 			hash_val = h.hexdigest()
# 			try:
# 				f = Resource.objects.get(hash_val=hash_val)
# 			except Resource.DoesNotExist:
# 				pass
# 			else:
# 				os.remove(file.link)
# 				return f
#
# 		file.creator = self.context['request'].user
# 		file.hash_val = hash_val
# 		file.hash_type = hash_type
# 		for key, val in validated_data.items():
# 			setattr(file, key, val)
# 		file.save()
# 		return file
#
#
# class ResourceDownloadSerializer(serializers.Serializer):
# 	id = serializers.IntegerField(write_only=True)
# 	href = serializers.URLField(read_only=True)
#
# 	def to_representation(self, instance):
# 		ret = dict(link_type=instance.get_link_type_display())
# 		if instance.link_type == Resource.LINK_TYPE_HTTP:
# 			ret['href'] = instance.link
# 		elif instance.link_type == Resource.LINK_TYPE_TEXT:
# 			ret['text'] = open(instance.link).read(4096).encode('utf8')
# 		elif instance.link_type == Resource.LINK_TYPE_FILE:
# 			expire = 3600 * 24
# 			key = '{}{}'.format(instance.hash_val, random.randint(1e4, 1e5 - 1))
# 			cache.set(key, instance.id, expire)
# 			ret['href'] = reverse('resource-download', args=[key, ])
# 			ret['expire'] = expire
# 		return ret
#
#
# class MaterialSerializer(serializers.ModelSerializer):
# 	TMP_FILE = os.path.join(settings.RESOURCE_ROOT, 'material_tmp')
#
# 	# write
# 	stream = serializers.FileField(write_only=True)
# 	hash_val = serializers.SlugField(required=False)
# 	hash_type = serializers.SlugField(required=False)
#
# 	# read
# 	uri = serializers.URLField(read_only=True)
#
# 	def create(self, validated_data):
# 		# parse
# 		stream = validated_data.pop('stream')
# 		hash_val, hash_type = validated_data.pop('hash_val', None), validated_data.pop('hash_type', None)
#
# 		# save file and calc hash value
# 		tmp_file = '{}{}'.format(self.TMP_FILE, random.randint(1e4, 1e5 - 1))
# 		if hash_val and hash_type == 'sha256':
# 			try:
# 				f = Material.objects.get(hash_val=hash_val)
# 			except Material.DoesNotExist:
# 				extension = stream.name.split('.')[-1]
# 				filename = os.path.join(settings.RESOURCE_ROOT, '{}.{}'.format(hash_val, extension))
# 				with open(filename, 'wb') as fp:
# 					for chunk in stream.chunks(4096):
# 						fp.write(chunk)
# 			else:
# 				return f
# 		else:
# 			h, hash_type = sha256(), 'sha256'
# 			with open(tmp_file, 'wb') as fp:
# 				for chunk in stream.chunks(4096):
# 					h.update(chunk)
# 					fp.write(chunk)
#
# 			hash_val = h.hexdigest()
# 			try:
# 				f = Material.objects.get(hash_val=hash_val)
# 			except Material.DoesNotExist:
# 				extension = stream.name.split('.')[-1]
# 				filename = os.path.join(settings.RESOURCE_ROOT, '{}.{}'.format(hash_val, extension))
# 				os.rename(tmp_file, filename)
# 			else:
# 				os.remove(tmp_file)
# 				return f
#
# 		return super().create(dict(size=stream.size, hash_val=hash_val, hash_type=hash_type,
# 								   link=os.path.join(settings.RESOURCE_URL, '{}.{}'.format(hash_val, extension)),
# 								   link_type=Material.get_link_type(extension), format=extension,
# 								   ))
#
# 	class Meta:
# 		model = Material
# 		fields = ['stream', 'hash_val', 'hash_type', 'uri', ]
