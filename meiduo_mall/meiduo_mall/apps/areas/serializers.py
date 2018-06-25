from rest_framework import serializers

from .models import Area


class AreaSerialzier(serializers.ModelSerializer):
    """
    行政区划信息序列化器
    """
    class Meta:
        model = Area
        fields = ('id','name')


class SubAreaSerializer(serializers.ModelSerializer):
    """
    子行政区信息序列化器
    """
    subs = AreaSerialzier(many=True,read_only=True)


    class Meta:
        model = Area
        fields = ('id','name','subs')