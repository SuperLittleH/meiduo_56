from django.shortcuts import render
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView

from goods.models import SKU
from users import serializers


class SKUListView(ListAPIView):
    """
    sku列表数据
    """
    serializer_class = serializers.SKUSerializer
    filter_backends = (OrderingFilter)
    ordering_fields = ('create_time,price,sales')
    
    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id,is_launched=True)
