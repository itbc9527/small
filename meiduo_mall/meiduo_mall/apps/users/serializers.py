# -*- coding:utf-8 -*-
# @File  :serializers.py
# @Author:bc
# @Date  :18-10-26
# @Desc  :
import re
from django_redis import get_redis_connection
from rest_framework import serializers
from users.models import User
from utils.utils import gen_jwt


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


class ValidateUsernameSerializser(serializers.Serializer):
    """验证用户名"""
    username = serializers.CharField(label="用户名", min_length=5, max_length=20)

    def validate_username(self, value):
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            self.context['view'].count = 0
            return value
        else:
            self.context['view'].count = 1
            raise serializers.ValidationError("该用户已经注册")


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


class UserLoginSerializer(ValidateMobileSerializser, ValidateUsernameSerializser):
    """用户注册"""
    password = serializers.CharField(label="密码", min_length=8, max_length=20, write_only=True)
    password2 = serializers.CharField(label="确认密码", min_length=8, max_length=20)

    sms_code = serializers.CharField(label="短信验证码", min_length=6, max_length=6)
    allow = serializers.BooleanField(label="同意协议")

    def validate(self, attrs):
        if attrs.get('allow') is False:
            raise serializers.ValidationError("请同意协议")

        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError("两次密码输入不一致")

        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get("sms_%s" % attrs.get('mobile'))
        if not real_sms_code:
            raise serializers.ValidationError('验证码过期')
        if real_sms_code.decode() != attrs.get('sms_code'):
            raise serializers.ValidationError('验证码错误')

        return attrs

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            mobile=validated_data['mobile'],
        )
        user.set_password(validated_data['password'])
        user.save()
        token = gen_jwt(user)
        user.token = token
        return user


class AuthorizateSerializer(serializers.Serializer):
    username = serializers.CharField(label="用户名", min_length=5, max_length=20, required=False)
    password = serializers.CharField(label="密码", min_length=8, max_length=20, write_only=True)
    mobile = serializers.CharField(label='手机号', max_length=11, min_length=11, required=False)

    @staticmethod
    def check_and_sign(user, attrs):
        user.check_password(attrs['password'])
        token = gen_jwt(user)
        attrs['token'] = token
        return attrs

    def validate(self, attrs):
        try:
            user = User.objects.get(username=attrs["username"])
        except User.DoesNotExist:
            try:
                user = User.objects.get(mobile=attrs["username"])
            except User.DoesNotExist:
                raise serializers.ValidationError("该用户不存在")
            else:
                return self.check_and_sign(user, attrs)
        else:
            return self.check_and_sign(user, attrs)





