import requests
import hmac, hashlib
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from order.models import Order


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment(request):
    order_id = request.data.get('order_id')
    if not order_id:
        return Response({'detail': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    
    order = get_object_or_404(Order, id=order_id, user=request.user)

    
    phone = request.data.get('phone') or getattr(getattr(request.user, 'profile', None), 'phone_number', None)
    if not phone:
        return Response({'detail': 'User phone number not available. Provide "phone" in POST body.'}, status=status.HTTP_400_BAD_REQUEST)

    # optional: save provided phone to user.profile if requested and profile exists
    save_phone = request.data.get('save_phone')
    if save_phone and hasattr(request.user, 'profile'):
        try:
            request.user.profile.phone_number = phone
            request.user.profile.save()
        except Exception:
            # non-fatal: don't block payment if saving fails
            pass

    payload = {
        "amount": float(order.total_amount),
        "currency": "TZS",
        "email": getattr(request.user, 'email', ''),
        "phone": phone,
        "callback_url": settings.ZENOPAY_CALLBACK_URL
    }

    headers = {
        "Authorization": f"Bearer {settings.ZENOPAY_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post("https://api.zeno.co.tz/pay", json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        response_data = resp.json()
    except requests.RequestException as exc:
        return Response({'detail': 'Payment provider error', 'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    with transaction.atomic():
        order.payment_reference = response_data.get('reference') or response_data.get('id')
        order.provider_session_id = response_data.get('session_id') or response_data.get('session')  # provider-specific
        order.payment_status = 'processing'
        order.save()

    return Response({"payment_url": response_data.get("payment_url")})



@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def payment_callback(request):
    sig_header = request.headers.get('X-Zenopay-Signature')  # example header name
    secret = getattr(settings, 'ZENOPAY_WEBHOOK_SECRET', None)
    if secret:
        computed = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, sig_header or ''):
            return Response({'detail': 'invalid signature'}, status=status.HTTP_403_FORBIDDEN)

    payload = request.data
    reference = payload.get('reference') or payload.get('id') or payload.get('payment_reference')
    provider_session = payload.get('session_id') or payload.get('session')

    if not reference:
        return Response({'detail': 'reference is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        order = Order.objects.get(payment_reference=reference)
    except Order.DoesNotExist:
        # try lookup by provider_session_id maybe
        try:
            order = Order.objects.get(provider_session_id=provider_session)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found for reference'}, status=status.HTTP_404_NOT_FOUND)

    # idempotent: if already marked paid, do nothing
    if order.payment_status == 'paid':
        return Response({'message': 'already paid'})

    status_val = payload.get('status')
    if status_val in ('success', 'completed', 'paid'):
        order.payment_status = 'paid'
        order.status = 'paid'
    elif status_val in ('failed', 'cancelled', 'declined'):
        order.payment_status = 'failed'
        order.status = 'cancelled'
    else:
        # non-final (pending)
        order.payment_status = 'processing'
    order.save()
    return Response({'message': 'ok'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    # This view is a placeholder — return a simple list of order IDs
    return Response({'orders': [o.id for o in orders]})



