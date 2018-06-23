from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from oauth.exceptions import QQAPIError
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

# /oauth/qq/user/
class QQAuthUserView(APIView):
    """
    QQ登录的用户
    """
    def get(self,request):
        """
        获取qq登录的用户数据
        :param request:
        :return:
        """
        code = request.query_params.get('code')
        if not code:
            return Response({'message':'缺少code'},status=status.HTTP_400_BAD_REQUEST)

        oauth = OAuthQQ()

        # 获取用户的openid
        try:
            access_token = oauth.get_access_token(code)
            openid = oauth.get_openid(access_token)
        except QQAPIError:
            return Response({'message':'QQ服务异常'},status=status.HTTP_503_SERVICE_UNAVAILABLE)