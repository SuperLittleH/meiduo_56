from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.views import APIView
from django.http import HttpResponse

from meiduo_mall.libs.captcha.captcha import captcha
from verifications import constants

# Create your views here.

# url('^image_codes/(?P<image_code_id>[\w-]+)/$', views.ImageCodeView.as_view()),
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