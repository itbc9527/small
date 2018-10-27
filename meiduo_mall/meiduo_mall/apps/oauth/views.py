from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from oauth.models import OauthQQUser
from oauth.serializers import QQAuthLoginSerializer
from utils.utils import gen_jwt
from .utils import QQLoginUtils


class QQAuthURLView(APIView):

    def get(self, request):
        next_url = request.query_params.get('next')
        oauth = QQLoginUtils(state=next_url)
        url = oauth.qq_login_url()
        return Response({"login_url": url}, status=status.HTTP_200_OK)


class QQAuthLoginView(CreateAPIView):
    serializer_class = QQAuthLoginSerializer

    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'message': '缺少参数'}, status=status.HTTP_400_BAD_REQUEST)

        oauth = QQLoginUtils()
        access_token = oauth.get_access_token(code)
        openid = oauth.get_openid(access_token)

        try:
            oauth = OauthQQUser.objects.get(openid=openid)
        except OauthQQUser.DoesNotExist:
            access_token = oauth.generate_save_user_token(openid)
            data = {'access_token': access_token}
        else:
            user = oauth.user
            token = gen_jwt(user)
            data = {
                "username": user.username,
                "user_id": user.id,
                "token": token
            }
        return Response(data, status=status.HTTP_200_OK)
