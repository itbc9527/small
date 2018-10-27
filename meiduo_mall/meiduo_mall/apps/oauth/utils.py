# -*- coding:utf-8 -*-
# @File  :utils.py
# @Author:bc
# @Date  :18-10-27
# @Desc  :
import json
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen

import logging
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer, BadData

logger = logging.getLogger('django')


class QQAPIError(Exception):
    pass


class QQLoginUtils(object):

    def __init__(self, client_id=None, redirect_uri=None, state=None, client_secret=None):
        self.client_id = client_id or settings.QQ_CLIENT_ID
        self.client_secret = client_secret or settings.QQ_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.QQ_REDIRECT_URI
        self.state = state or settings.QQ_STATE

    def qq_login_url(self):
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope': 'get_user_info'
        }

        url = 'https://graph.qq.com/oauth2.0/authorize?' + urlencode(params)
        return url

    def get_access_token(self, code):
        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            'code': code,
            "redirect_uri": self.redirect_uri
        }

        url = 'https://graph.qq.com/oauth2.0/token?' + urlencode(params)
        response = urlopen(url)
        response_data = response.read().decode()
        data = parse_qs(response_data)

        access_token = data.get('access_token')
        if not access_token:
            logger.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIError
        return access_token[0]

    def get_openid(self, access_token):
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token
        response = urlopen(url)
        response_data = response.read().decode()
        data = json.loads(response_data[10:-4])
        openid = data.get('openid')
        if not openid:
            logger.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIError
        return openid

    @staticmethod
    def generate_save_user_token(openid):
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 300)
        data = {"openid": openid}
        access_token = serializer.dumps(data)
        return access_token.decode()

    @staticmethod
    def check_access_token(access_token):
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 300)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        return data.get('openid')