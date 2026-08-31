import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Address
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
def address(user):
    return Address.objects.create(
        user=user,
        full_name="Jane Doe",
        phone_number="+919812345678",
        street_address="123 MG Road",
        city="Pune",
        state="Maharashtra",
        postal_code="411001",
        country="India",
        is_default=True,
    )


@pytest.fixture
def product():
    return Product.objects.create(
        name="Diamond Stud Earrings",
        category="earrings",
        base_price="50000.00",
        tax_percentage="3.00",
        total_stock=10,
        is_active=True,
    )


def _add_to_cart(client, product, quantity=1):
    return client.post(reverse("orders:cart-item-list"), {"product_id": product.id, "quantity": quantity})


class TestCheckout:
    def test_requires_authentication(self, client):
        response = client.post(reverse("orders:checkout"), {"address_id": 1})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_checkout_empty_cart_rejected(self, client, user, address):
        client.force_authenticate(user=user)
        response = client.post(reverse("orders:checkout"), {"address_id": address.id})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_checkout_with_another_users_address_rejected(self, client, user, product):
        other_user = User.objects.create_user(email="other@example.com", password="StrongPass123!")
        other_address = Address.objects.create(
            user=other_user, full_name="Other", phone_number="+919999999999",
            street_address="X", city="X", state="X", postal_code="000000", country="India",
        )
        client.force_authenticate(user=user)
        _add_to_cart(client, product)
        response = client.post(reverse("orders:checkout"), {"address_id": other_address.id})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_checkout_success_creates_pending_order_with_razorpay_order(self, client, user, address, product):
        client.force_authenticate(user=user)
        _add_to_cart(client, product, quantity=2)

        response = client.post(reverse("orders:checkout"), {"address_id": address.id})
        assert response.status_code == status.HTTP_201_CREATED

        order_data = response.data["order"]
        assert order_data["status"] == "pending_payment"
        assert order_data["subtotal"] == "100000.00"
        assert order_data["tax_amount"] == "3000.00"
        assert order_data["total_amount"] == "103000.00"
        assert len(order_data["items"]) == 1

        razorpay_data = response.data["razorpay"]
        assert razorpay_data["razorpay_order_id"] == f"order_fake_{order_data['id']}"
        assert razorpay_data["amount"] == 10300000  # paise
        assert "key_id" in razorpay_data

        # Cart is empty afterward.
        cart_response = client.get(reverse("orders:cart"))
        assert cart_response.data["items"] == []

        # Stock is NOT decremented at checkout — only after verified payment.
        product.refresh_from_db()
        assert product.total_stock == 10

    def test_checkout_razorpay_failure_still_leaves_order_saved(self, client, user, address, product, mock_razorpay_order):
        mock_razorpay_order.side_effect = Exception("Razorpay is down")
        client.force_authenticate(user=user)
        _add_to_cart(client, product)

        response = client.post(reverse("orders:checkout"), {"address_id": address.id})
        assert response.status_code == status.HTTP_502_BAD_GATEWAY

        from orders.models import Order
        assert Order.objects.filter(user=user, status="pending_payment").exists()

    def test_price_change_after_checkout_does_not_affect_past_order(self, client, user, address, product):
        client.force_authenticate(user=user)
        _add_to_cart(client, product, quantity=1)
        checkout_response = client.post(reverse("orders:checkout"), {"address_id": address.id})
        order_id = checkout_response.data["order"]["id"]

        product.base_price = "999999.00"
        product.save(update_fields=["base_price"])

        detail_response = client.get(reverse("orders:order-detail", args=[order_id]))
        assert detail_response.data["items"][0]["product_price"] == "50000.00"


class TestOrderHistory:
    def test_user_only_sees_own_orders(self, client, user, address, product):
        other_user = User.objects.create_user(email="other@example.com", password="StrongPass123!")

        client.force_authenticate(user=user)
        _add_to_cart(client, product)
        client.post(reverse("orders:checkout"), {"address_id": address.id})

        client.force_authenticate(user=other_user)
        response = client.get(reverse("orders:order-list"))
        assert response.data["count"] == 0

    def test_order_list_and_detail(self, client, user, address, product):
        client.force_authenticate(user=user)
        _add_to_cart(client, product)
        create_response = client.post(reverse("orders:checkout"), {"address_id": address.id})
        order_id = create_response.data["order"]["id"]

        list_response = client.get(reverse("orders:order-list"))
        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.data["count"] == 1

        detail_response = client.get(reverse("orders:order-detail", args=[order_id]))
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["id"] == order_id

    def test_cannot_patch_order_status_via_api(self, client, user, address, product):
        client.force_authenticate(user=user)
        _add_to_cart(client, product)
        create_response = client.post(reverse("orders:checkout"), {"address_id": address.id})
        order_id = create_response.data["order"]["id"]

        response = client.patch(reverse("orders:order-detail", args=[order_id]), {"status": "shipped"})
        assert response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED)
