import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

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
        name="Diamond Stud Earrings",
        category="earrings",
        base_price="50000.00",
        total_stock=10,
        is_active=True,
    )


@pytest.fixture
def sized_product():
    p = Product.objects.create(
        name="Solitaire Ring",
        category="rings",
        base_price="200000.00",
        total_stock=0,
        is_active=True,
    )
    p.sizes.create(size="6", stock=3)
    p.sizes.create(size="7", stock=0)
    return p


class TestCartAccess:
    def test_requires_authentication(self, client):
        response = client.get(reverse("orders:cart"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_cart_created_lazily(self, client, user):
        client.force_authenticate(user=user)
        response = client.get(reverse("orders:cart"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["items"] == []
        assert response.data["total_amount"] == "0.00"


class TestAddToCart:
    def test_add_item_success(self, client, user, product):
        client.force_authenticate(user=user)
        response = client.post(
            reverse("orders:cart-item-list"),
            {"product_id": product.id, "quantity": 2},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["total_items"] == 2
        assert response.data["items"][0]["quantity"] == 2

    def test_add_item_exceeding_stock_rejected(self, client, user, product):
        client.force_authenticate(user=user)
        response = client.post(
            reverse("orders:cart-item-list"),
            {"product_id": product.id, "quantity": 999},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_item_twice_increments_quantity_not_duplicates(self, client, user, product):
        client.force_authenticate(user=user)
        client.post(reverse("orders:cart-item-list"), {"product_id": product.id, "quantity": 1})
        response = client.post(reverse("orders:cart-item-list"), {"product_id": product.id, "quantity": 1})
        assert len(response.data["items"]) == 1
        assert response.data["items"][0]["quantity"] == 2

    def test_sized_product_requires_size(self, client, user, sized_product):
        client.force_authenticate(user=user)
        response = client.post(
            reverse("orders:cart-item-list"),
            {"product_id": sized_product.id, "quantity": 1},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sized_product_respects_per_size_stock(self, client, user, sized_product):
        client.force_authenticate(user=user)
        response = client.post(
            reverse("orders:cart-item-list"),
            {"product_id": sized_product.id, "size": "7", "quantity": 1},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = client.post(
            reverse("orders:cart-item-list"),
            {"product_id": sized_product.id, "size": "6", "quantity": 2},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_inactive_product_cannot_be_added(self, client, user, product):
        product.is_active = False
        product.save(update_fields=["is_active"])
        client.force_authenticate(user=user)
        response = client.post(
            reverse("orders:cart-item-list"),
            {"product_id": product.id, "quantity": 1},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUpdateAndRemoveCartItem:
    def _add(self, client, product, quantity=1):
        return client.post(
            reverse("orders:cart-item-list"), {"product_id": product.id, "quantity": quantity}
        )

    def test_update_quantity(self, client, user, product):
        client.force_authenticate(user=user)
        add_response = self._add(client, product, quantity=1)
        item_id = add_response.data["items"][0]["id"]

        response = client.patch(
            reverse("orders:cart-item-detail", args=[item_id]), {"quantity": 5}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["items"][0]["quantity"] == 5

    def test_remove_item(self, client, user, product):
        client.force_authenticate(user=user)
        add_response = self._add(client, product, quantity=1)
        item_id = add_response.data["items"][0]["id"]

        response = client.delete(reverse("orders:cart-item-detail", args=[item_id]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["items"] == []

    def test_cannot_touch_another_users_cart_item(self, client, user, product):
        other_user = User.objects.create_user(email="other@example.com", password="StrongPass123!")
        client.force_authenticate(user=user)
        add_response = self._add(client, product, quantity=1)
        item_id = add_response.data["items"][0]["id"]

        client.force_authenticate(user=other_user)
        response = client.patch(reverse("orders:cart-item-detail", args=[item_id]), {"quantity": 2})
        assert response.status_code == status.HTTP_404_NOT_FOUND
