from random import randint
from django.http import HttpResponse

# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from celery_tasks.sms.tasks import send_sms_code
from .serializers import SmsCodeSerializer, ValidateMobileSerializser, ValidateUsernameSerializser, UserLoginSerializer, \
    AuthorizateSerializer
from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.utils import constants


class LoginRegisterMixin(object):
    """序列化校验"""
    def get_serializer(self, **kwargs):
        serializer = self.serializer_class(data=kwargs, context={'view': self})
        serializer.is_valid(raise_exception=True)
        return serializer

    def get_value(self, value):
        return getattr(self, value, None)


class LoginRegisterAPIView(LoginRegisterMixin, APIView):
    """自定义登陆注册视图"""
    def get(self, request, auto_value=False, value_str='count', **kwargs):
        serializer = self.get_serializer(**kwargs)

        if not auto_value:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            kwargs.update({value_str: self.get_value(value_str)})
            return Response(kwargs, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.get_serializer(**request.data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ImageCodeView(View):
    """图片验证码"""
    def get(self, request, image_code_id):
        # 生成图片验证码
        name, text, image = captcha.generate_captcha()
        print("图片验证码:", text)

        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        return HttpResponse(image, content_type='images/jpg')


class SmsCodeView(LoginRegisterMixin, APIView):
    serializer_class = SmsCodeSerializer

    def get(self, request, mobile):
        data = {
            "text": request.query_params.get('text'),
            "image_code_id": request.query_params.get('image_code_id'),
            "mobile": mobile
        }

        self.get_serializer(**data)

        sms_code = "%06d" % randint(0, 999999)
        print("短信验证码", sms_code)

        pl = get_redis_connection('verify_codes').pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()
        # celery 发送短信验证码 -> 测试通过
        # sms_code_expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        # send_sms_code.delay(mobile, sms_code, sms_code_expires)
        return Response({"message": "OK"})


class ValidateMobileView(LoginRegisterAPIView):
    serializer_class = ValidateMobileSerializser

    def get(self, request, mobile):
        return super().get(request, auto_value=True, mobile=mobile)


class ValidateUsernameView(LoginRegisterAPIView):
    serializer_class = ValidateUsernameSerializser

    def get(self, request, username):
        return super().get(request, auto_value=True, username=username)


class UserLoginView(GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        data = {
            "id": user.id,
            "username": user.username,
            "token": user.token
        }
        return Response(data, status=status.HTTP_200_OK)


class AuthorizateView(LoginRegisterAPIView):
    """支持手机号与用户名两种方式登陆"""
    serializer_class = AuthorizateSerializer

