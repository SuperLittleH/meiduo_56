from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from users import constants
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


class AddressViewSet(CreateModelMixin,UpdateModelMixin,GenericViewSet):
    """
    用户地址新增与删除
    """
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_delete=False)


    def list(self,request,*args,**kwargs):
        """
        用户地址列表数据
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset,many=True)
        user = self.request.user
        return Response({
            'user_id':user.id,
            'default_address_id':user.default_address_id,
            'limit':constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses':serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        保存用户数据
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message':'保存地址数据已达到上限'},status=status.HTTP_400_BAD_REQUEST)

        return super().create(request,*args,**kwargs)

    def destroy(self,request,*args,**kwargs):
        """
        处理删除
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        address = self.get_object()

        #逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'],detail=True)
    def status(self,request,pk=None,address_id=None):
        """
        设置默认地值
        :param request:
        :param pk:
        :param address_id:
        :return:
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message':'OK'},status=status.HTTP_200_OK)

    @action(methods=['put'],detail=True)
    def title(self,request,pk=None,address_id=None):
        """
        修改标题
        :param request:
        :param pk:
        :param address_id:
        :return:
        """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)