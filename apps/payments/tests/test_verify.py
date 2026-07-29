import hashlib
import hmac

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
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
        name="Diamond Pendant", category="necklaces", base_price="30000.00", total_stock=5, is_active=True,
    )


@pytest.fixture
def pending_order(user, product):
    order = Order.objects.create(
        user=user,
        address_full_name="Jane Doe", address_phone_number="+919812345678",
        address_street="123 MG Road", address_city="Pune", address_state="Maharashtra",
        address_postal_code="411001", address_country="India",
        status="pending_payment",
        subtotal="30000.00", tax_amount="0.00", total_amount="30000.00",
        razorpay_order_id="order_test123",
    )
    OrderItem.objects.create(
        order=order, product=product, product_name=product.name, product_sku=product.sku,
        product_price="30000.00", quantity=1,
    )
    return order


def _sign(razorpay_order_id, razorpay_payment_id, secret):
    payload = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class TestVerifyPayment:
    def test_requires_authentication(self, client):
        response = client.post(reverse("payments:verify"), {
            "razorpay_order_id": "x", "razorpay_payment_id": "y", "razorpay_signature": "z",
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_valid_signature_marks_order_paid_and_decrements_stock(self, client, user, pending_order, product, settings):
        settings.RAZORPAY_KEY_SECRET = "test_key_secret"
        signature = _sign(pending_order.razorpay_order_id, "pay_test123", "test_key_secret")

        client.force_authenticate(user=user)
        response = client.post(reverse("payments:verify"), {
            "razorpay_order_id": pending_order.razorpay_order_id,
            "razorpay_payment_id": "pay_test123",
            "razorpay_signature": signature,
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "paid"

        pending_order.refresh_from_db()
        assert pending_order.razorpay_payment_id == "pay_test123"
        assert pending_order.stock_decremented_at is not None

        product.refresh_from_db()
        assert product.total_stock == 4

    def test_tampered_signature_rejected(self, client, user, pending_order, settings):
        settings.RAZORPAY_KEY_SECRET = "test_key_secret"
        client.force_authenticate(user=user)
        response = client.post(reverse("payments:verify"), {
            "razorpay_order_id": pending_order.razorpay_order_id,
            "razorpay_payment_id": "pay_test123",
            "razorpay_signature": "not-the-real-signature",
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        pending_order.refresh_from_db()
        assert pending_order.status == "pending_payment"

    def test_calling_verify_twice_does_not_double_decrement(self, client, user, pending_order, product, settings):
        settings.RAZORPAY_KEY_SECRET = "test_key_secret"
        signature = _sign(pending_order.razorpay_order_id, "pay_test123", "test_key_secret")
        client.force_authenticate(user=user)
        payload = {
            "razorpay_order_id": pending_order.razorpay_order_id,
            "razorpay_payment_id": "pay_test123",
            "razorpay_signature": signature,
        }

        client.post(reverse("payments:verify"), payload)
        client.post(reverse("payments:verify"), payload)  # frontend retries, or double-click

        product.refresh_from_db()
        assert product.total_stock == 4  # decremented once, not twice

    def test_cannot_verify_another_users_order(self, client, pending_order, settings):
        settings.RAZORPAY_KEY_SECRET = "test_key_secret"
        other_user = User.objects.create_user(email="other@example.com", password="StrongPass123!")
        signature = _sign(pending_order.razorpay_order_id, "pay_test123", "test_key_secret")

        client.force_authenticate(user=other_user)
        response = client.post(reverse("payments:verify"), {
            "razorpay_order_id": pending_order.razorpay_order_id,
            "razorpay_payment_id": "pay_test123",
            "razorpay_signature": signature,
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

        pending_order.refresh_from_db()
        assert pending_order.status == "pending_payment"

    def test_late_payment_after_reservation_expired_still_succeeds(self, client, user, pending_order, product, settings):
        """The reservation window is internal bookkeeping, not proof of
        payment — if Razorpay confirms the money actually moved, we must
        honor it even if our own reservation lapsed a moment earlier."""
        settings.RAZORPAY_KEY_SECRET = "test_key_secret"
        pending_order.status = "expired"
        pending_order.save(update_fields=["status"])

        signature = _sign(pending_order.razorpay_order_id, "pay_test123", "test_key_secret")
        client.force_authenticate(user=user)
        response = client.post(reverse("payments:verify"), {
            "razorpay_order_id": pending_order.razorpay_order_id,
            "razorpay_payment_id": "pay_test123",
            "razorpay_signature": signature,
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "paid"

        product.refresh_from_db()
        assert product.total_stock == 4
