from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from accounts.models import Address
from orders.models import Order

User = get_user_model()

pytestmark = pytest.mark.django_db


def _make_order(user, address, *, status, reservation_expires_at):
    return Order.objects.create(
        user=user,
        address_full_name=address.full_name, address_phone_number=address.phone_number,
        address_street=address.street_address, address_city=address.city,
        address_state=address.state, address_postal_code=address.postal_code,
        address_country=address.country,
        status=status, subtotal="1000.00", tax_amount="0.00", total_amount="1000.00",
        reservation_expires_at=reservation_expires_at,
    )


@pytest.fixture
def user():
    return User.objects.create_user(email="shopper@example.com", password="StrongPass123!")


@pytest.fixture
def address(user):
    return Address.objects.create(
        user=user, full_name="Jane Doe", phone_number="+919812345678",
        street_address="123 MG Road", city="Pune", state="Maharashtra",
        postal_code="411001", country="India",
    )


class TestExpireStaleReservations:
    def test_expires_only_lapsed_pending_orders(self, user, address):
        now = timezone.now()
        lapsed = _make_order(user, address, status="pending_payment", reservation_expires_at=now - timedelta(minutes=1))
        active = _make_order(user, address, status="pending_payment", reservation_expires_at=now + timedelta(minutes=10))
        already_paid = _make_order(user, address, status="paid", reservation_expires_at=now - timedelta(minutes=1))

        call_command("expire_stale_reservations")

        lapsed.refresh_from_db()
        active.refresh_from_db()
        already_paid.refresh_from_db()

        assert lapsed.status == "expired"
        assert active.status == "pending_payment"
        assert already_paid.status == "paid"  # untouched — was never "pending_payment"

    def test_running_twice_is_a_safe_no_op(self, user, address):
        _make_order(
            user, address, status="pending_payment",
            reservation_expires_at=timezone.now() - timedelta(minutes=1),
        )
        call_command("expire_stale_reservations")
        call_command("expire_stale_reservations")  # should just find nothing left to expire
