from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

admin.site.site_header = 'AfriSokoni Admin'
admin.site.site_title = "AfriSokoni Admin Portal"

@api_view(['GET'])
def api_root(request, format=None): 
        return Response({
                'orders': reverse('my-orders', request=request, format=format),
                
                'payment': reverse('initiate_payment', request=request, format=format),
        })


urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/order/', include('order.urls')),
        path('api/payment/', include('payment.urls')),
    
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
        path('', api_root),
]
