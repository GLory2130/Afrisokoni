from django.db import models
from django.contrib.auth.models import User
from products.models import Product  # assuming you have a Product model
from django.contrib.auth import get_user_model

User = get_user_model()

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('paid', 'Paid'), ('cancelled', 'Cancelled')],
        default='pending'
    )
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('mpesa','M-Pesa'),
            ('mixx','Mixx by Yas'),
            ('airtel','Airtel Money'),
            ('halopesa','HaloPesa'),
            ('card','Credit Card'),
        ],
        default='mpesa'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending','Pending'),('processing','Processing'),('paid','Paid'),('failed','Failed')],
        default='pending'
    )
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    provider_session_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
