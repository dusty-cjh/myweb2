import hmac
from rest_framework import serializers
from .settings import ONE_BOT


class EventSerializer(serializers.Serializer):
    POST_TYPE = (
        'message', 'notice', 'request', 'meta_event',
    )

    time = serializers.IntegerField()
    self_id = serializers.IntegerField()
    post_type = serializers.ChoiceField(choices=POST_TYPE)

    def validate(self, attrs):
        # HMAC verification
        request = self.context['request']
        sign = hmac.new(ONE_BOT['secret_key'], request.body, 'sha1').hexdigest()
        req_sign = request.headers['X-Signature'][len('sha1='):]
        if req_sign != sign:
            raise serializers.ValidationError('invalid request signature: %s', req_sign)

        # return
        return super().validate(attrs)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        instance.update(validated_data)
        return instance


class SenderSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    sex = serializers.ChoiceField(choices=('male', 'female'))
    age = serializers.IntegerField()

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        instance.update(validated_data)
        return instance


class MessageSerializer(EventSerializer):
    MESSAGE_TYPE = (
        'private', 'group',
    )

    message_type = serializers.ChoiceField(choices=MESSAGE_TYPE, required=True)
    sub_type = serializers.ChoiceField(choices=[], required=True)
    message_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    message = serializers.CharField()
    raw_message = serializers.CharField()
    font = serializers.IntegerField(required=False)
    sender = SenderSerializer


class OneBotSerializer(serializers.Serializer):
    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        instance.update(validated_data)
        return instance


class OneBotRequest(OneBotSerializer):
    def validate(self, attrs):
        # HMAC verification
        request = self.context['request']
        sign = hmac.new(ONE_BOT['secret_key'], request.body, 'sha1').hexdigest()
        req_sign = request.headers['X-Signature'][len('sha1='):]
        if req_sign != sign:
            raise serializers.ValidationError('invalid request signature: %s', req_sign)

        # return
        return super().validate(attrs)
    pass


class OneBotResponse(OneBotSerializer):
    message_id = serializers.IntegerField()


class SendPrivateMsgRequest(OneBotRequest):
    user_id = serializers.IntegerField()
    group_id = serializers.IntegerField(required=False)
    message = serializers.CharField()
    auto_escape = serializers.BooleanField(default=False)


class SendPrivateMsgResponse(OneBotResponse):
    pass


class SendGroupMsgRequest(OneBotRequest):
    group_id = serializers.IntegerField()
    message = serializers.CharField()
    auto_escape = serializers.BooleanField(default=False)


class SendGroupMsgResponse(OneBotResponse):
    pass


class ReceivedPrivateMsgRequest(MessageSerializer):
    SUB_TYPE = (
        'friend', 'group', 'group_self', 'other',
    )

    sub_type = serializers.ChoiceField(choices=SUB_TYPE)
    temp_source = serializers.CharField(required=False)
    message_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    message = serializers.CharField()
    raw_message = serializers.CharField()
    font = serializers.IntegerField()
    sender = SenderSerializer()


class RequestEventSerializer(EventSerializer):
    REQUEST_TYPE = ('friend', 'group')

    request_type = serializers.ChoiceField(choices=REQUEST_TYPE)


class RequestFriendRequest(RequestEventSerializer):
    user_id = serializers.IntegerField()
    comment = serializers.CharField()
    flag = serializers.CharField()


class RequestFriendResponse(OneBotSerializer):
    approve = serializers.BooleanField(allow_null=True)
    remark = serializers.CharField(allow_null=True)


class RequestGroupRequest(RequestEventSerializer):
    SUB_TYPE = ('add', 'invite')

    sub_type = serializers.ChoiceField(choices=SUB_TYPE)
    group_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    comment = serializers.CharField()
    flag = serializers.CharField()


class RequestGroupResponse(OneBotSerializer):
    approve = serializers.BooleanField(allow_null=True)
    reason = serializers.CharField(allow_null=True)


class ReplySerializer(serializers.Serializer):
    reply = serializers.CharField()
    auto_escape = serializers.BooleanField(default=False)
