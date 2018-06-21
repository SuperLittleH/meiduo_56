from django.shortcuts import render
from rest_framework.views import APIView

# Create your views here.

# url('^image_codes/(?P<image_code_id>[\w-]+)/$', views.ImageCodeView.as_view()),
class ImageCodeView(APIView):
    """
    图片验证码
    """
