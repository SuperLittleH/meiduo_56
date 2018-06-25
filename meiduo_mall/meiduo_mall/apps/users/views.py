from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
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


class EmailView(UpdateAPIView):
    """
    保存用户邮箱
    """
    # 序列化器
    serializer_class = serializers.EmailSerializer
    # 权限
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    """
    邮箱验证
    """
    def get(self,request):
        #获取token
        token = request.query_params.get('token')
        if not token:
            return Response({'message':'缺少token'},status=status.HTTP_400_BAD_REQUEST)

        # 验证token
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message':'链接信息无效'},status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()
            return Response({'message':'OK'})

