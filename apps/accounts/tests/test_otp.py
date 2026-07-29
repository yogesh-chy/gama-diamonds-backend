from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import EmailOTP

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    """Throttle/cooldown state lives in the cache; isolate each test."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client():
    return APIClient()


def _request_otp(client, email="shopper@example.com"):
    return client.post(reverse("accounts:otp_request"), {"email": email})


class TestRequestOTP:
    def test_request_otp_sends_email_and_creates_record(self, client):
        response = _request_otp(client)
        assert response.status_code == status.HTTP_200_OK
        assert EmailOTP.objects.filter(email="shopper@example.com").exists()
        assert len(mail.outbox) == 1
        assert "login code" in mail.outbox[0].subject.lower()

    def test_request_otp_does_not_reveal_whether_account_exists(self, client, django_user_model):
        existing = django_user_model.objects.create_user(email="known@example.com")
        r1 = _request_otp(client, "known@example.com")
        r2 = _request_otp(client, "unknown@example.com")
        assert r1.status_code == r2.status_code == status.HTTP_200_OK
        assert r1.data == r2.data

    def test_request_otp_invalid_email_rejected(self, client):
        response = client.post(reverse("accounts:otp_request"), {"email": "not-an-email"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_resend_before_cooldown_is_rejected(self, client):
        first = _request_otp(client)
        assert first.status_code == status.HTTP_200_OK
        second = _request_otp(client)
        assert second.status_code == status.HTTP_400_BAD_REQUEST

    def test_new_request_invalidates_previous_code(self, client):
        with mock.patch("accounts.services._generate_code", return_value="111111"):
            _request_otp(client)
        first_otp = EmailOTP.objects.get(email="shopper@example.com")
        assert not first_otp.is_used

        # bypass cooldown by clearing cache, as if enough time had passed
        from django.core.cache import cache
        cache.clear()

        with mock.patch("accounts.services._generate_code", return_value="222222"):
            _request_otp(client)
        first_otp.refresh_from_db()
        assert first_otp.is_used is True


class TestVerifyOTP:
    def _get_code_and_request(self, client, email="shopper@example.com", code="482913"):
        with mock.patch("accounts.services._generate_code", return_value=code):
            _request_otp(client, email)
        return code

    def test_verify_creates_user_and_returns_tokens(self, client):
        code = self._get_code_and_request(client)
        response = client.post(reverse("accounts:otp_verify"), {"email": "shopper@example.com", "code": code})
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["is_staff"] is False
        assert response.data["user"]["is_email_verified"] is True
        user = User.objects.get(email="shopper@example.com")
        assert user.has_usable_password() is False

    def test_verify_existing_user_returns_200_not_201(self, client, django_user_model):
        django_user_model.objects.create_user(email="returning@example.com")
        code = self._get_code_and_request(client, email="returning@example.com")
        response = client.post(reverse("accounts:otp_verify"), {"email": "returning@example.com", "code": code})
        assert response.status_code == status.HTTP_200_OK

    def test_verify_wrong_code_rejected_and_counts_attempt(self, client):
        self._get_code_and_request(client, code="482913")
        response = client.post(reverse("accounts:otp_verify"), {"email": "shopper@example.com", "code": "000000"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        otp = EmailOTP.objects.get(email="shopper@example.com")
        assert otp.attempts == 1
        assert otp.is_used is False

    def test_verify_locks_after_max_attempts(self, client, settings):
        settings.OTP_MAX_ATTEMPTS = 3
        self._get_code_and_request(client, code="482913")
        for _ in range(3):
            client.post(reverse("accounts:otp_verify"), {"email": "shopper@example.com", "code": "000000"})
        otp = EmailOTP.objects.get(email="shopper@example.com")
        assert otp.is_used is True

        # even the correct code is now dead
        response = client.post(reverse("accounts:otp_verify"), {"email": "shopper@example.com", "code": "482913"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_expired_code_rejected(self, client):
        code = self._get_code_and_request(client, code="482913")
        otp = EmailOTP.objects.get(email="shopper@example.com")
        otp.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        otp.save(update_fields=["expires_at"])

        response = client.post(reverse("accounts:otp_verify"), {"email": "shopper@example.com", "code": code})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_without_prior_request_rejected(self, client):
        response = client.post(reverse("accounts:otp_verify"), {"email": "nobody@example.com", "code": "123456"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_exposes_is_staff_true_for_admin(self, client, django_user_model):
        admin = django_user_model.objects.create_superuser(email="admin@example.com", password="unused")
        code = self._get_code_and_request(client, email="admin@example.com")
        response = client.post(reverse("accounts:otp_verify"), {"email": "admin@example.com", "code": code})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"]["is_staff"] is True


class TestTokenRefreshAndLogout:
    def _login(self, client, email="shopper@example.com"):
        code = "482913"
        with mock.patch("accounts.services._generate_code", return_value=code):
            _request_otp(client, email)
        return client.post(reverse("accounts:otp_verify"), {"email": email, "code": code}).data

    def test_refresh_issues_new_access_token(self, client):
        tokens = self._login(client)
        response = client.post(reverse("accounts:token_refresh"), {"refresh": tokens["refresh"]})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_logout_blacklists_refresh_token(self, client):
        tokens = self._login(client)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        logout_response = client.post(reverse("accounts:logout"), {"refresh": tokens["refresh"]})
        assert logout_response.status_code == status.HTTP_205_RESET_CONTENT

        reuse_response = client.post(reverse("accounts:token_refresh"), {"refresh": tokens["refresh"]})
        assert reuse_response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMe:
    def test_me_requires_authentication(self, client):
        response = client.get(reverse("accounts:me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_authenticated_user(self, client, django_user_model):
        user = django_user_model.objects.create_user(email="shopper@example.com")
        client.force_authenticate(user=user)
        response = client.get(reverse("accounts:me"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
