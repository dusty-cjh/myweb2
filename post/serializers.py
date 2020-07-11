from rest_framework import serializers

from .models import Summary


class SummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Summary
        fields = '__all__'

