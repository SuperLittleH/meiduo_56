from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User
from . import serializers
# Create your views here.


class UsernameCountView(APIView):
    """
      用户名数量
    """
    def get(self,request,username):
        """
        获取用户名数量
        :param request:
        :param username:
        :return:
        """
        count = User.objects.filter(username=username).count()
        data = {
            'username':username,
            'count':count
        }

        return Response(data)


class MobileCountView(APIView):
    """
    手机号数量
    """
    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


class UserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = serializers.CreateUserSerializer

class UserDetailView(RetrieveAPIView):
    """
    用户详情视图
    """
    serializer_class = serializers.UserDetailSerializer
    # 权限只有登陆用户才能进入
    permission_classes = [IsAuthenticated]

    # 重写get_object
    def get_object(self):
        # 返回用户
        return self.request.user