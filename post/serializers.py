from rest_framework import serializers

from .models import Summary, Post


class SummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Summary
        fields = '__all__'
        read_only_fields = ['id', 'pv', 'uv', 'created_time', ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(dict(id=instance.id))
        return data


class PostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

