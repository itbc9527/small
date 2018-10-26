# -*- coding:utf-8 -*-
# @File  :urls.py
# @Author:bc
# @Date  :18-10-26
# @Desc  :
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^image_codes/(?P<image_code_id>[\w-]+)/$", views.ImageCodeView.as_view()),
    url(r"^mobiles/(?P<mobile>[\d]+)/count/$", views.ValidateMobileView.as_view()),
    url(r'^sms_codes/(?P<mobile>[\d]+)/$', views.SmsCodeView.as_view()),
]
