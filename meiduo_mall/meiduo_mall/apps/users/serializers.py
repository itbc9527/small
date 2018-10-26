# -*- coding:utf-8 -*-
# @File  :serializers.py
# @Author:bc
# @Date  :18-10-26
# @Desc  :
import re

from django_redis import get_redis_connection
from rest_framework import serializers

from users.models import User


class ValidateMobileSerializser(serializers.Serializer):
    mobile = serializers.CharField(label='手机号', required=True, max_length=11, min_length=11)

    def validate_mobile(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        try:
            user = User.objects.get(mobile=value)
        except User.DoesNotExist:
            self.context['view'].count = 0
            return value
        else:
            self.context['view'].count = 1
            raise serializers.ValidationError("手机号已经被注册")


class SmsCodeSerializer(ValidateMobileSerializser):
    """短信验证码"""
    text = serializers.CharField(label='图片验证码', required=True, max_length=4, min_length=4)
    image_code_id = serializers.UUIDField(label='uuid', required=True)

    class Meta:
        fields = ('mobile', 'text', 'image_code_id')

    def validate(self, attrs):
        text = attrs.get('text')
        image_code_id = attrs.get('image_code_id')
        mobile = attrs.get('mobile')
        if not all((text, image_code_id)):
            raise serializers.ValidationError("缺少参数")
        redis_conn = get_redis_connection('verify_codes')

        real_text = redis_conn.get("img_%s" % image_code_id)
        if not real_text:
            raise serializers.ValidationError('验证码过期')
        if real_text.decode().upper() != text.upper():
            raise serializers.ValidationError('验证码错误')
        send_flag = redis_conn.get("send_flag_%s" % mobile)
        if send_flag:
            raise serializers.ValidationError('请求过于频繁')
        redis_conn.delete("img_%s" % image_code_id)
        return attrs






