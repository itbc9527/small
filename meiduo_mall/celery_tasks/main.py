# -*- coding:utf-8 -*-
# @File  :main.py
# @Author:bc
# @Date  :18-10-26
# @Desc  :
from celery import Celery

import os
if not os.getenv("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = 'meiduo_mall.settings.dev'

celery_app = Celery("meiduo")
celery_app.config_from_object('celery_tasks.config')

celery_app.autodiscover_tasks(['celery_tasks.sms'])

