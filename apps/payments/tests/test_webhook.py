import hashlib
import hmac
import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from payments.models import WebhookEvent
from products.models import Product

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(email="shopper@example.com", password="StrongPass123!")


@pytest.fixture
def product():
    return Product.objects.create(
        name="Diamond Bracelet", category="bracelets", base_price="40000.00", total_stock=5, is_active=True,
    )


@pytest.fixture
def pending_order(user, product):
    order = Order.objects.create(
        user=user,
        address_full_name="Jane Doe", address_phone_number="+919812345678",
        address_street="123 MG Road", address_city="Pune", address_state="Maharashtra",
        address_postal_code="411001", address_country="India",
        status="pending_payment",
        subtotal="40000.00", tax_amount="0.00", total_amount="40000.00",
        razorpay_order_id="order_test123",
    )
    OrderItem.objects.create(
        order=order, product=product, product_name=product.name, product_sku=product.sku,
        product_price="40000.00", quantity=1,
    )
    return order


def _captured_payload(order_id, payment_id):
    return {
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": payment_id, "order_id": order_id}}},
    }


def _post_webhook(client, payload, secret, signature_override=None):
    body = json.dumps(payload).encode()
    signature = signature_override or hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return client.generic(
        "POST", reverse("payments:webhook"), data=body, content_type="application/json",
        HTTP_X_RAZORPAY_SIGNATURE=signature,
    )


class TestWebhookSignature:
    def test_invalid_signature_rejected(self, client, pending_order, settings):
        settings.RAZORPAY_WEBHOOK_SECRET = "webhook_secret"
        payload = _captured_payload(pending_order.razorpay_order_id, "pay_abc")
        response = _post_webhook(client, payload, "webhook_secret", signature_override="wrong-signature")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        pending_order.refresh_from_db()
        assert pending_order.status == "pending_payment"


class TestWebhookProcessing:
    def test_payment_captured_marks_order_paid_and_decrements_stock(self, client, pending_order, product, settings):
        settings.RAZORPAY_WEBHOOK_SECRET = "webhook_secret"
        payload = _captured_payload(pending_order.razorpay_order_id, "pay_abc")

        response = _post_webhook(client, payload, "webhook_secret")
        assert response.status_code == status.HTTP_200_OK

        pending_order.refresh_from_db()
        assert pending_order.status == "paid"
        assert pending_order.stock_decremented_at is not None

        product.refresh_from_db()
        assert product.total_stock == 4

    def test_redelivered_webhook_does_not_double_decrement(self, client, pending_order, product, settings):
        settings.RAZORPAY_WEBHOOK_SECRET = "webhook_secret"
        payload = _captured_payload(pending_order.razorpay_order_id, "pay_abc")

        _post_webhook(client, payload, "webhook_secret")
        _post_webhook(client, payload, "webhook_secret")  # Razorpay redelivers

        assert WebhookEvent.objects.count() == 1
        product.refresh_from_db()
        assert product.total_stock == 4  # decremented once, not twice

    def test_payment_failed_marks_order_payment_failed(self, client, pending_order, settings):
        settings.RAZORPAY_WEBHOOK_SECRET = "webhook_secret"
        payload = {
            "event": "payment.failed",
            "payload": {"payment": {"entity": {"id": "pay_failed_1", "order_id": pending_order.razorpay_order_id}}},
        }
        response = _post_webhook(client, payload, "webhook_secret")
        assert response.status_code == status.HTTP_200_OK

        pending_order.refresh_from_db()
        assert pending_order.status == "payment_failed"

    def test_unknown_order_id_returns_200_not_error(self, client, settings):
        """Razorpay retries on non-2xx — an order we can't match to (yet,
        or ever) shouldn't trigger endless retries."""
        settings.RAZORPAY_WEBHOOK_SECRET = "webhook_secret"
        payload = _captured_payload("order_does_not_exist", "pay_xyz")
        response = _post_webhook(client, payload, "webhook_secret")
        assert response.status_code == status.HTTP_200_OK
