from decimal import Decimal
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import serializers
from django.db import transaction
import logging

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods

logger = logging.getLogger('django')


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)

class SaveOrderSerializer(serializers.ModelSerializer):
    """
    下单序列化器
    """
    class Meta:
        model = OrderInfo
        fields = ('order_id','address','pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """
        保存订单
        :param validated_data:
        :return:
        """
        #获取当前下单用户
        user = self.context['request'].user

        # 生成订单编号
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        # 保存订单基本信息数据 OrderInfo
        address = validated_data['address']
        pay_method = validated_data['pay_method']
        with transaction.atomic():
            #创建一个保存点
            save_id = transaction.savepoint()

            try:
                # 创建订单信息
                order = OrderInfo.objects.create(
                    order_id = order_id,
                    user = user,
                    address = address,
                    total_count = 0,
                    total_amount = Decimal(0),
                    freight = Decimal(10),
                    pay_method = pay_method,
                    status = OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH'] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )

                # 获取购物车信息
                redis_conn = get_redis_connection('cart')
                # 哈希信息
                redis_cart = redis_conn.hgetall('cart_%s' % user.id)
                # 表格信息
                cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

                # 讲Bytes类型转换为int
                cart = {}
                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(redis_cart[sku_id])

                # 一次查出所有商品数据
                skus = SKU.objects.filter(id__in=cart.keys())

                # 遍历结算商品
                # 处理订单商品
                for sku in skus:
                    sku_count = cart[sku.id]

                    # 判断库存
                    # 原始库存
                    orgin_stock = sku.stock
                    # 原始销量
                    orgin_sales = sku.sales

                    # 判断商品库存是否充足
                    if sku_count > orgin_stock:
                        transaction.savepoint_rollback(save_id)
                        raise serializers.ValidationError('商品库存不足')

                    # 用于演示并发下单
                    # import time
                    # time.sleep(5)


                    # 减少库存 增加销量
                    new_stock = orgin_stock - sku_count
                    new_sales = orgin_sales + sku_count

                    sku.stock = new_stock
                    sku.sales = new_sales
                    sku.save()

                    # 累计商品的SPU销量信息
                    sku.goods.sales += sku_count
                    sku.goods.save()

                    # 累计订单基本信息的数据
                    order.total_count += sku_count #累计总金额
                    order.total_amount += (sku.price * sku_count) #累计总额
                    # 保存订单商品数据
                    OrderGoods.objects.create(
                        order = order,
                        sku = sku,
                        count = sku_count,
                        price = sku.price,
                    )

                # 更新订单的金额数量信息
                order.total_amount += order.freight
                order.save()

            except serializers.ValidationError:
                raise
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)
                raise

            #提交事务
            transaction.savepoint_commit(save_id)

            # 更新redis中保存的购物车数据
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *cart_selected)
            pl.srem('cart_selected_%s' % user.id, *cart_selected)
            pl.execute()

            return order
