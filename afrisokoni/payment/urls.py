from django.urls import path
from .views import initiate_payment

urlpatterns = [
    path('initiate/', initiate_payment, name='initiate_payment'),
]
