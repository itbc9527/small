# -*- coding:utf-8 -*-
# @File  :serializers.py
# @Author:bc
# @Date  :18-10-27
# @Desc  :
from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.models import OauthQQUser
from oauth.utils import QQLoginUtils
from users.models import User
from users.serializers import ValidateMobileSerializser
from utils.utils import gen_jwt


class QQAuthLoginSerializer(ValidateMobileSerializser):
    sms_code = serializers.CharField(label="短信验证码", min_length=6, max_length=6, write_only=True)
    password = serializers.CharField(label="密码", min_length=8, max_length=20, write_only=True)
    access_token = serializers.CharField(label='access_token', write_only=True)
    username = serializers.CharField(label='用户名', read_only=True)
    id = serializers.IntegerField(label='user_id', read_only=True)

    def validate(self, attrs):
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get("sms_%s" % attrs.get('mobile'))
        if not real_sms_code:
            raise serializers.ValidationError('验证码过期')
        if real_sms_code.decode() != attrs.get('sms_code'):
            raise serializers.ValidationError('验证码错误')

        openid = QQLoginUtils.check_access_token(attrs['access_token'])
        if not openid:
            raise serializers.ValidationError("access_token错误")
        attrs['openid'] = openid

        mobile = attrs['mobile']
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            user = User.objects.create_user(username=mobile, mobile=mobile, password=attrs['password'])
        else:
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError("密码输入错误")

        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        openid = validated_data['openid']
        user = validated_data.get('user')

        OauthQQUser.objects.create(user=user, openid=openid)

        token = gen_jwt(user)
        user.token = token
        return user