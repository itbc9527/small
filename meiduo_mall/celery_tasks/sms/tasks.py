# -*- coding:utf-8 -*-
# @File  :tasks.py
# @Author:bc
# @Date  :18-10-26
# @Desc  :
import logging
import os
BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
sys.path.insert(0, BASE_PATH)

from celery_tasks.main import celery_app
from meiduo_mall.libs.yuntongxun.sms import CCP

logger = logging.getLogger('django')

SMS_CODE_TEMP_ID = 1


@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, code, expires):
    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [code, expires], SMS_CODE_TEMP_ID)
    except Exception as e:
        logger.error("发送验证码短信[异常][ mobile: %s, message: %s ]" % (mobile, e))
    else:
        if result == 0:
            logger.info("发送验证码短信[正常][ mobile: %s ]" % mobile)
        else:
            logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)