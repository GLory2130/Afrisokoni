from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product
from django.db import transaction


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']


class OrderItemSerializer(serializers.ModelSerializer):
    # read: full product data; write: supply product_id
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'product_id', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    # set user from request automatically
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'total_amount', 'status', 'created_at']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('Order must contain at least one item.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        # user is provided via HiddenField (CurrentUserDefault)
        user = validated_data.pop('user')

        # compute total from the products/prices to avoid trusting client input
        total = 0
        for item in items_data:
            product = item['product']
            qty = item.get('quantity', 1)
            total += (product.price or 0) * qty

        order = Order.objects.create(user=user, total_amount=total, **validated_data)

        # create order items
        for item in items_data:
            product = item['product']
            qty = item.get('quantity', 1)
            OrderItem.objects.create(order=order, product=product, quantity=qty)

        return order
