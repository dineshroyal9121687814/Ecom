from rest_framework import serializers
from .models import Product, Category, Customer
from .models import Cart, CartItem


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'desc',
            'price',
            'original_price',
            'discount_percentage',
            'quantity'
        ]

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity  # Already in INR
