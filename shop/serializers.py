import time, json
import logging
from django.urls import reverse
from django.utils.translation import gettext as _
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from wechat.mixin import WeChatCommonMixin
from manager import wechat_manager
from .models import Goods, Order, Appraise


class GoodsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goods
        fields = '__all__'

    def to_representation(self, instance):
        res = super().to_representation(instance)
        url = reverse('shop:goods', args=(instance.id, ))
        res['url'] = url
        return res


class OrderSerializer(WeChatCommonMixin, serializers.ModelSerializer):
    params = None
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    extra_data = serializers.JSONField(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

    def create(self, validated_data):
        if validated_data['goods'].nums < 1:
            raise ValidationError("库存不足！")
        request = self.context['request']
        validated_data['user'] = request.user
        obj = super().create(validated_data)
        notify_url = '{}://{}{}'.format(request.scheme, settings.DOMAIN, reverse('shop:order-create-callback'))
        openid = self.context['request'].user.username
        kwargs = {
            'title': obj.goods.title,
            'price': obj.goods.price,
            'notify_url': notify_url,
            'openid': openid,
            'attach': str(obj.id),
        }
        self.params = wechat_manager.create_js_prepay_order(**kwargs)
        request.log.info('shop.OrderSerializer.create|kwargs={}|return={}', kwargs, self.params)
        request.log.data('api|order-create|data={}', validated_data)

        # save recent used address of user to session
        try:
            request.session['user_address'] = json.loads(validated_data['address'])
        except json.JSONDecodeError:
            raise ValidationError(_('invalid_format|user-address is not a json-string'))

        return obj

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if self.params is not None:
            rep.update(self.params)
        return rep


class AppraiseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Appraise
        fields = '__all__'

    def create(self, validated_data):
        request = self.context['request']
        request.log.data('api|appraise-create|data={}', validated_data)
        return super().create(validated_data)