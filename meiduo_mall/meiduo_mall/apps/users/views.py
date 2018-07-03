from django.shortcuts import render
from django.http import HttpResponse
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, GenericAPIView
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.views import ObtainJSONWebToken

from goods.models import SKU
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
    用户详情
    """
    # 序列化器
    serializer_class = serializers.UserDetailSerializer
    # IsAuthenticated 仅通过认证的用户
    permission_classes = [IsAuthenticated]


    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    """
    保存用户邮箱
    """
    # 序列化器
    serializer_class = serializers.EmailSerializer
    # 权限只限登陆用户进入
    permission_classes = [IsAuthenticated]

    # 重写get_object
    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    """
    邮箱验证
    """
    def get(self,request):
        # 获取token
        token = request.query_params.get('token')
        if not token:
            return Response({'message':'缺少token'},status=status.HTTP_400_BAD_REQUEST)

        # 校验token
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
    permission = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

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
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        保存用户数据
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        #检查用户地址数据数目不能给超过上限
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
        设置默认地址
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


class UserBrowsingHistoryView(CreateModelMixin, GenericAPIView):
    """
    用户浏览历史记录
    """
    serializer_class = serializers.AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        保存
        """
        return self.create(request)

    def get(self,request):
        """
        获取
        :param request:
        :return:
        """
        user_id = request.user.id

        redis_conn = get_redis_connection("history")
        history = redis_conn.lrange("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT)
        # print(history)
        skus = []
        # 为了保持查询出的顺序与用户的浏览历史保持顺序一致
        for sku_id in history:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        serializer = serializers.SKUSerializer(skus,many=True)
        return Response(serializer.data)


class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户认证
    """
    def post(self, request, *args, **kwargs):
        #调用父类方法获取jwt默认处理结果
        response = super().post(request, *args, **kwargs)

        # 仿照drf jwt 扩展对用户的认证
        #如果用户登陆认证成功，则合并购物车
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            response = merge_cart_cookie_to_redis(request, user, response)

        return response