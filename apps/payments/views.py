from django.db import transaction
from django.views.generic import TemplateView
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from orders import services as order_services
from orders.models import Order
from orders.serializers import OrderSerializer

from .models import WebhookEvent
from .serializers import PaymentVerifySerializer
from .signature import verify_checkout_signature, verify_webhook_signature


class VerifyPaymentView(APIView):
    """
    POST /api/payments/verify/ — called by the frontend immediately after
    the Razorpay Checkout widget reports success. Recomputes the HMAC
    signature server-side and only trusts that — never the frontend's
    "success" claim alone (TRD Section 6, step 5).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not verify_checkout_signature(
            data["razorpay_order_id"], data["razorpay_payment_id"], data["razorpay_signature"]
        ):
            raise ValidationError({"detail": "Payment signature verification failed."})

        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(razorpay_order_id=data["razorpay_order_id"])
            except Order.DoesNotExist:
                raise ValidationError({"detail": "No matching order found for this payment."})

            if order.user_id != request.user.id:
                # Signature is genuinely valid but doesn't belong to this
                # account — never let user A mark user B's order paid.
                raise PermissionDenied()

            if order.status in ("pending_payment", "expired"):
                # "expired" is included deliberately: if the reservation
                # window lapsed a moment before Razorpay's confirmation
                # reached us, the customer still paid — we must honor
                # that regardless of our internal reservation bookkeeping,
                # even if it means this sale oversells a since-reserved
                # unit. Never leave a genuinely paid order stuck unfulfilled.
                order.status = "paid"
                order.razorpay_payment_id = data["razorpay_payment_id"]
                order.save(update_fields=["status", "razorpay_payment_id", "updated_at"])
                order_services.decrement_stock_for_order(order)
            # else: already paid — /verify/ was called twice, or the
            # webhook beat it there. Return current state; don't
            # re-decrement (decrement_stock_for_order is also itself
            # idempotent via stock_decremented_at as a second guard).

        return Response(OrderSerializer(order).data)


class RazorpayWebhookView(APIView):
    """
    POST /api/payments/webhook/ — backup confirmation path for cases where
    the user closes the browser before /verify/ fires (TRD Section 6,
    step 7). Verified with a secret SEPARATE from /verify/'s (step 8).
    Public by design — Razorpay calls this, not an authenticated user —
    but nothing in the payload is trusted until the signature checks out.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_body = request.body  # must read before request.data touches the stream
        received_signature = request.headers.get("X-Razorpay-Signature", "")

        if not verify_webhook_signature(raw_body, received_signature):
            return Response({"detail": "Invalid webhook signature."}, status=status.HTTP_400_BAD_REQUEST)

        payload = request.data
        event_type = payload.get("event", "")
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_payment_id = payment_entity.get("id", "")
        razorpay_order_id = payment_entity.get("order_id", "")

        if not razorpay_payment_id:
            return Response({"detail": "Malformed payload."}, status=status.HTTP_400_BAD_REQUEST)

        # Idempotency guard against webhook redelivery.
        _, created = WebhookEvent.objects.get_or_create(
            event_type=event_type,
            razorpay_payment_id=razorpay_payment_id,
            defaults={"razorpay_order_id": razorpay_order_id, "payload": payload},
        )
        if not created:
            return Response({"detail": "Already processed."}, status=status.HTTP_200_OK)

        with transaction.atomic():
            order = Order.objects.select_for_update().filter(razorpay_order_id=razorpay_order_id).first()
            if order is None:
                # Nothing to reconcile against (yet) — still 200 so
                # Razorpay doesn't retry indefinitely for an order that
                # will never exist on our side.
                return Response({"detail": "No matching order."}, status=status.HTTP_200_OK)

            if event_type == "payment.captured" and order.status in ("pending_payment", "expired"):
                order.status = "paid"
                order.razorpay_payment_id = razorpay_payment_id
                order.save(update_fields=["status", "razorpay_payment_id", "updated_at"])
                order_services.decrement_stock_for_order(order)
            elif event_type == "payment.failed" and order.status == "pending_payment":
                order.status = "payment_failed"
                order.save(update_fields=["status", "updated_at"])

        return Response({"detail": "ok"}, status=status.HTTP_200_OK)


class TestCheckoutPageView(TemplateView):
    """
    DEV-ONLY manual smoke-test page for the Razorpay integration — lets you
    log in, add a product to cart, check out, and pay with Razorpay's test
    cards, without needing the real Next.js frontend built yet. Talks to
    this same Django server directly (same-origin fetch calls), so it does
    NOT require ngrok — only the webhook (a separate, backup path) needs a
    public URL. Only ever mounted when DEBUG=True (see payments/urls.py).
    """
    template_name = "payments/test_checkout.html"
