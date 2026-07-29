import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Address

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_a():
    return User.objects.create_user(email="a@example.com", password="StrongPass123!")


@pytest.fixture
def user_b():
    return User.objects.create_user(email="b@example.com", password="StrongPass123!")


def _address_payload(**overrides):
    payload = {
        "full_name": "Jane Doe",
        "phone_number": "+919812345678",
        "street_address": "123 MG Road",
        "city": "Pune",
        "state": "Maharashtra",
        "postal_code": "411001",
        "country": "India",
        "is_default": True,
    }
    payload.update(overrides)
    return payload


class TestAddressCRUD:
    def test_requires_authentication(self, client):
        response = client.get(reverse("accounts:address-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_and_list_own_address(self, client, user_a):
        client.force_authenticate(user=user_a)
        create_response = client.post(reverse("accounts:address-list"), _address_payload())
        assert create_response.status_code == status.HTTP_201_CREATED

        list_response = client.get(reverse("accounts:address-list"))
        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.data["count"] == 1

    def test_only_one_default_address_per_user(self, client, user_a):
        client.force_authenticate(user=user_a)
        client.post(reverse("accounts:address-list"), _address_payload())
        client.post(reverse("accounts:address-list"), _address_payload(full_name="Second Address"))

        defaults = Address.objects.filter(user=user_a, is_default=True)
        assert defaults.count() == 1
        assert defaults.first().full_name == "Second Address"


class TestAddressOwnershipIsolation:
    def test_user_cannot_view_another_users_address(self, client, user_a, user_b):
        client.force_authenticate(user=user_a)
        create_response = client.post(reverse("accounts:address-list"), _address_payload())
        address_id = create_response.data["id"]

        client.force_authenticate(user=user_b)
        detail_response = client.get(reverse("accounts:address-detail", args=[address_id]))
        assert detail_response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_cannot_delete_another_users_address(self, client, user_a, user_b):
        client.force_authenticate(user=user_a)
        create_response = client.post(reverse("accounts:address-list"), _address_payload())
        address_id = create_response.data["id"]

        client.force_authenticate(user=user_b)
        delete_response = client.delete(reverse("accounts:address-detail", args=[address_id]))
        assert delete_response.status_code == status.HTTP_404_NOT_FOUND
        assert Address.objects.filter(id=address_id).exists()
