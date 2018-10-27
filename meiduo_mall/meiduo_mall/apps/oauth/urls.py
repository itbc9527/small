# -*- coding:utf-8 -*-
# @File  :urls.py
# @Author:bc
# @Date  :18-10-27
# @Desc  :
from django.conf.urls import url

from oauth import views

urlpatterns = [
    url(r'^oauth/qq/authorization/$', views.QQAuthURLView.as_view()),
    url(r'oauth/qq/user/$', views.QQAuthLoginView.as_view()),
]