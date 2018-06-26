from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .models import Area
from areas import serializers


class AreaViewSet(CacheResponseMixin,ReadOnlyModelViewSet):
    """
    行政区划信息
    """
    pagination_class = None #区划信息不分页

    def get_queryset(self):
        """
        提供数据集合
        :return: 返回数据集合
        """
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        """
        改写提供序列化器的方法
        :return:
        """
        if self.action == 'list':
            return serializers.AreaSerialzier
        else:
            return serializers.SubAreaSerializer