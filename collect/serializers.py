import json
from django.urls import reverse
from rest_framework import serializers

from wechat.serializers import WeChatPayMixin
from .models import StudyCollect, VersionConfig


class StudyCollectSerializer(WeChatPayMixin, serializers.ModelSerializer):
    class Meta:
        model = StudyCollect
        fields = '__all__'
        read_only_fields = ['created_time', 'status']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['owner'] = user
        instance = super().create(validated_data)

        # 创建微信预付单
        version = VersionConfig.objects.get(version=instance.version)
        self.create_prepay(total_fee=round(version.fee * 100),
                           notify_url=reverse('collect:signup-result'),
                           attach=json.dumps({'id': instance.id, 'version': instance.version, }),
                           )

        return instance

