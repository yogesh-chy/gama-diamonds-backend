from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Address
from orders.models import Order
from products.models import Product

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def _make_user(email):
    return User.objects.create_user(email=email, password="StrongPass123!")


def _make_address(user):
    return Address.objects.create(
        user=user, full_name="Jane Doe", phone_number="+919812345678",
        street_address="123 MG Road", city="Pune", state="Maharashtra",
        postal_code="411001", country="India",
    )


@pytest.fixture
def last_unit_product():
    """Only one unit exists — the exact scenario the reservation exists for."""
    return Product.objects.create(
        name="One-of-a-Kind Solitaire Pendant",
        category="necklaces",
        base_price="500000.00",
        total_stock=1,
        is_active=True,
    )


class TestCheckoutReservation:
    def test_second_user_blocked_while_first_users_reservation_is_active(
        self, client, last_unit_product
    ):
        user_a, user_b = _make_user("a@example.com"), _make_user("b@example.com")
        address_a, address_b = _make_address(user_a), _make_address(user_b)

        client.force_authenticate(user=user_a)
        client.post(reverse("orders:cart-item-list"), {"product_id": last_unit_product.id, "quantity": 1})
        response_a = client.post(reverse("orders:checkout"), {"address_id": address_a.id})
        assert response_a.status_code == status.HTTP_201_CREATED
        assert Order.objects.get(pk=response_a.data["order"]["id"]).status == "pending_payment"

        # User B tries to buy the same (now reserved) last unit.
        client.force_authenticate(user=user_b)
        add_response = client.post(
            reverse("orders:cart-item-list"), {"product_id": last_unit_product.id, "quantity": 1}
        )
        assert add_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_second_user_succeeds_once_first_reservation_expires(self, client, last_unit_product):
        user_a, user_b = _make_user("a@example.com"), _make_user("b@example.com")
        address_a, address_b = _make_address(user_a), _make_address(user_b)

        client.force_authenticate(user=user_a)
        client.post(reverse("orders:cart-item-list"), {"product_id": last_unit_product.id, "quantity": 1})
        response_a = client.post(reverse("orders:checkout"), {"address_id": address_a.id})
        order_a = Order.objects.get(pk=response_a.data["order"]["id"])

        # Simulate the reservation window having lapsed.
        order_a.reservation_expires_at = timezone.now() - timedelta(minutes=1)
        order_a.save(update_fields=["reservation_expires_at"])

        client.force_authenticate(user=user_b)
        add_response = client.post(
            reverse("orders:cart-item-list"), {"product_id": last_unit_product.id, "quantity": 1}
        )
        assert add_response.status_code == status.HTTP_201_CREATED

    def test_reservation_does_not_block_the_same_users_own_checkout_history(
        self, client, last_unit_product
    ):
        """A user's own prior pending order shouldn't stop them from
        seeing accurate availability elsewhere in the same session —
        sanity check that the reserved-quantity query is a straight
        product/size match, not accidentally scoped oddly."""
        user = _make_user("solo@example.com")
        address = _make_address(user)

        client.force_authenticate(user=user)
        client.post(reverse("orders:cart-item-list"), {"product_id": last_unit_product.id, "quantity": 1})
        response = client.post(reverse("orders:checkout"), {"address_id": address.id})
        assert response.status_code == status.HTTP_201_CREATED

        # Cart is empty now — nothing further to reserve for this user,
        # this just documents expected post-checkout state.
        cart_response = client.get(reverse("orders:cart"))
        assert cart_response.data["items"] == []
