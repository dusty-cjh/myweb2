import os
import hashlib
from django.conf import settings
from rest_framework import serializers

from .models import Material


class MaterialSerializer(serializers.Serializer):

    sha3 = serializers.SlugField(max_length=128, required=False, help_text='文件哈希值')
    file = serializers.FileField(required=True, write_only=True, label='选择文件')
    url = serializers.CharField(required=False, read_only=True, label='访问链接')

    def create(self, validated_data):
        sha3 = validated_data.get('sha3')
        file = validated_data['file']

        instance = Material.create(file, sha3)
        return instance

    def to_representation(self, instance):
        return instance.data
