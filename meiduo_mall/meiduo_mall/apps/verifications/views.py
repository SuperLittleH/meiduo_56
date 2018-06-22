import random
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from rest_framework import status
import logging

from meiduo_mall.libs.captcha.captcha import captcha
from verifications import constants
from verifications import serializers
from meiduo_mall.utils.yuntongxun.sms import CCP
# Create your views here.
# url('^image_codes/(?P<image_code_id>[\w-]+)/$', views.ImageCodeView.as_view()),

logger = logging.getLogger('django')

class ImageCodeView(APIView):
    """
    图片验证码
    """
    def get(self,request,image_code_id):
        """
        获取短信验证码
        :param request:
        :param image_code_id:
        :return:
        """
        #生成图片验证码
        text,image = captcha.generate_captcha()

        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex("img_%s" % image_code_id,constants.IMAGE_CODE_REDIS_EXPIRES,text)
        # 固定返回验证码的图片数据不需要rest
        return HttpResponse(image,content_type="image/jpg")

    # url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),
class SMSCodeView(GenericAPIView):
    """
    短信验证码
    传入参数：
        mobile, image_code_id, text
    """
    serializer_class = serializers.ImageCodeCheckSerializer

    def get(self,request,mobile):
        """
        创建短信验证码
        :param request:
        :param mobile:
        :return:
        """
        # 判断短信验证码，判断是否在60s内
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 生成短信验证码
        sms_code = "%06d" % random.randint(0,999999)
        # 保存短信验证码和发送记录
        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES,sms_code)
        pl.setex("send_flag_%s" % mobile,constants.SEND_SMS_CODE_INTERVAL,1)
        pl.execute()

        # 发送短信验证码
        try:
            ccp = CCP()
            expires = constants.SMS_CODE_REDIS_EXPIRES // 60
            result = ccp.send_template_sms(mobile,[sms_code,expires],constants.SMS_CODE_TEMP_ID)
        except Exception as e:
            logger.error("发送验证码短信[异常][ mobile: %s, message: %s ]" % (mobile, e))
            return Response({'message':'failed'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            if result == 0:
                logger.info("发送验证码短信[正常][ mobile: %s ]" % mobile)
                return Response({'message':'OK'})
            else:
                logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)
                return Response({'message': 'failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


