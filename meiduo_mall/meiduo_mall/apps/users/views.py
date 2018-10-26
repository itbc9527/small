from random import randint

from copy import deepcopy
from django.http import HttpResponse

# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from celery_tasks.sms.tasks import send_sms_code

from .serializers import SmsCodeSerializer, ValidateMobileSerializser
from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.utils import constants


class ImageCodeView(View):
    """图片验证码"""
    def get(self, request, image_code_id):
        # 生成图片验证码
        name, text, image = captcha.generate_captcha()
        print("图片验证码:", text)

        # 保存文本信息
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        return HttpResponse(image, content_type='images/jpg')


class SmsCodeView(APIView):

    def get(self, request, mobile):
        data = {
            "text": request.query_params.get('text'),
            "image_code_id": request.query_params.get('image_code_id'),
            "mobile": mobile
        }
        serializer = SmsCodeSerializer(data=data, context={"view": self})
        serializer.is_valid(raise_exception=True)

        sms_code = "%06d" % randint(0, 999999)
        print("短信验证码", sms_code)
        # 保存短信验证码
        pl = get_redis_connection('verify_codes').pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()
        # celery 发送短信验证码 测试通过
        # sms_code_expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        # send_sms_code.delay(mobile, sms_code, sms_code_expires)
        return Response({"message": "OK"})


class ValidateMobileView(APIView):

    def get(self, request, mobile):
        serializer = ValidateMobileSerializser(data={"mobile": mobile}, context={"view": self})
        serializer.is_valid(raise_exception=True)
        return Response(data={"mobile": mobile, "count": self.count}, status=status.HTTP_200_OK)



