from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from oauth.utils import OAuthQQ

#  url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
class QQAuthURLView(APIView):
    """
    获取QQ登录的url
    """
    def get(self,request):
        """
        用户qq登录的url
        :param request:
        :return:
        """
        # 获取参数
        next = request.query_params.get('next')
        oauth = OAuthQQ(state=next)
        login_url = oauth.get_qq_login_url()
        return Response({'login_url':login_url})