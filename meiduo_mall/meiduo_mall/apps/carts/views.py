import base64
import pickle
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from carts import constants
from goods.models import SKU
from . import serializers

class CartView(APIView):
    """
    购物车
    """
    def perform_authentication(self, request):
        """
        重写父类的用户验证方法，不在进入视图前就检查jwt
        :param request:
        :return:
        """
        pass

    def post(self,request):
        """
        添加购物车
        :param request:
        :return:
        """
        serializer = serializers.CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        #尝试对请求的用户进行验证
        try:
            user = request.user
        except Exception:
            #验证失败,用户未登录
            user = None

        if user is not None and user.is_authenticated:
            #用户已登陆，在redis中保存
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 记录购物车商品数量
            pl.hincrby('cart_%s' % user.id, sku_id, count)
            #记录购物车的勾选项
            # 如果勾选
            if selected:
                pl.sadd('cart_selected_%s' % user.id,sku_id)
            pl.execute()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            # 用户未登录，在cookie中保存
            # {
            #     1001: { "count": 10, "selected": true},
            #     ...
            # }
            # 使用pickle序列化购物车数据，pickle操作的是bytes类型
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

            sku = cart.get(sku_id)
            if sku:
                count += int(sku.get('count'))

            cart[sku_id] = {
                'count':count,
                'selected':selected
            }

            cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()

            response = Response(serializer.data,status=status.HTTP_201_CREATED)

            #设置购物车的cookie
            #需要设置有效期，否则是临时cookie
            response.set_cookie('cart',cookie_cart,max_age=constants.CART_COOKIE_EXPIRES)

            return  response

    def get(self,request):
        """
        获取购物车内容
        :param request:
        :return:
        """
        # 查找user
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            #用户已登陆，从redis中读取
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            redis_cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
            cart = {}
            for sku_id,count in redis_cart.items():
                cart[int(sku_id)] = {
                    'count':count,
                    'selected':sku_id in redis_cart_selected
                }

        else:
            # 用户未登录，从cookie中获取
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

        # 遍历处理购物车数据
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]['count']
            sku.selected = cart[sku.id]['selected']

        serializer = serializers.CartSKUSerializer(skus,many=True)
        return Response(serializer.data)

    def put(self,request):
        """
        修改购物车数据
        :param request:
        :return:
        """
        # 接受参数校验参数
        serializer = serializers.CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 获取user
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            #用户已登陆购物车数据保存至redis
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 改变数量
            pl.hset('cart_%s' % user.id, sku_id, count)
            # 如果勾选
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            # 没勾选
            else:
                pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(serializer.data)
        else:
            # 用户未登录购物车数据在cookie中
            # 获取值
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

            cart[sku_id] = {
                'count':count,
                'selected':selected
            }
            cart_cookie = base64.b64encode(pickle.dumps(cart)).decode()

            response = Response(serializer.data)

            # 设置购物车的cookie和时间
            response.set_cookie('cart', cart_cookie, max_age=constants.CART_COOKIE_EXPIRES)
            return response


    def delete(self,request):
        """
        删除购物车数据
        :param request:
        :return:
        """
        serializer = serializers.CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data['sku_id']

        # 获取user
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登陆在redis保存
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, sku_id)
            pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            #用户未登录保存于cookie中
            #获取cookie
            response = Response(status=status.HTTP_204_NO_CONTENT)
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
                if sku_id in cart:
                    del cart[sku_id]
                    cookie_cort = base64.b64encode(pickle.dumps(cart)).decode()
                    # 设置cookie和有效期
                    response.set_cookie('cart', cookie_cort, max_age=constants.CART_COOKIE_EXPIRES)
            return response


class CartSelectAllView(APIView):
    """
    购物车全选
    """

    def perform_authentication(self, request):
        """
        重写父类的用户验证方法，不进入视图前就检查JWT
        :param request:
        :return:
        """
        pass

    def put(self, request):
        serializer = serializers.CartSelectAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data['selected']

        try:
            user = request.user
        except Exception:
            # 验证失败，用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登陆，在redis中保存
            redis_conn = get_redis_connection('cart')
            cart = redis_conn.hgetall('cart_%s' % user.id)
            sku_id_list = cart.keys()

            if selected:
                # 全选
                redis_conn.sadd('cart_selected_%s' % user.id, *sku_id_list)
            else:
                # 取消全选
                redis_conn.srem('cart_selected_%s' % user.id, *sku_id_list)
            return Response({'message': 'OK'})

        else:
            # 用户未登录
            cart = request.COOKIES.get('cart')

            response = Response({'message': 'OK'})

            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
                for sku_id in cart:
                    cart[sku_id]['selected'] = selected
                cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
                # 设置购物车的cookie
                # 需要设置有效期
                response.set_cookie('cart', cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)

            return response