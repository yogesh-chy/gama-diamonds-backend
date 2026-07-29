"""
Business logic for the OTP-based login/signup flow. Kept out of
views.py/serializers.py on purpose (same rationale as orders/services.py):
this is the part worth unit-testing without spinning up HTTP requests, and
the part most likely to need changes (SMS fallback, a different hashing
scheme, Celery-ified email) independent of the API surface.

Nothing in here trusts the frontend. The frontend's job is just to collect
an email and a 6-digit code and relay them.
"""
import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import serializers

from .models import EmailOTP

RESEND_COOLDOWN_CACHE_KEY = "otp:cooldown:{purpose}:{email}"


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_otp(email: str, code: str) -> str:
    """
    sha256(SECRET_KEY + email + code). SECRET_KEY acts as a pepper: even if
    the email_otps table leaks (backup exposure, SQLi, etc.) on its own, the
    codes can't be brute-forced offline without also having SECRET_KEY —
    the same defense-in-depth reasoning as Django's own password hasher
    salting, just cheaper since a 6-digit code doesn't need bcrypt-style
    slow hashing (the DB-level attempts counter is what stops online
    guessing, not hash cost).
    """
    payload = f"{settings.SECRET_KEY}:{email}:{code}".encode()
    return hashlib.sha256(payload).hexdigest()


def _generate_code() -> str:
    """Cryptographically secure, fixed-width, zero-padded numeric code."""
    upper_bound = 10 ** settings.OTP_LENGTH
    return str(secrets.randbelow(upper_bound)).zfill(settings.OTP_LENGTH)


def _cooldown_key(email: str, purpose: str) -> str:
    return RESEND_COOLDOWN_CACHE_KEY.format(purpose=purpose, email=email)


def seconds_until_resend_allowed(email: str, purpose: str = EmailOTP.Purpose.LOGIN) -> int:
    """
    Cache-backend-portable cooldown check: stores *when the cooldown ends*
    (an ISO timestamp) as the cache value rather than relying on
    cache.ttl(), which is a django-redis-only extension — LocMemCache (the
    dev/test fallback in base.py) doesn't implement it at all, so using it
    here would work in Docker-with-Redis and blow up everywhere else.
    """
    email = _normalize_email(email)
    allowed_at_iso = cache.get(_cooldown_key(email, purpose))
    if not allowed_at_iso:
        return 0
    allowed_at = timezone.datetime.fromisoformat(allowed_at_iso)
    remaining = (allowed_at - timezone.now()).total_seconds()
    return max(int(remaining), 0)


def request_otp(email: str, *, request_ip: str | None, purpose: str = EmailOTP.Purpose.LOGIN) -> EmailOTP:
    """
    Issues a new OTP for `email`, invalidating any still-live one for the
    same (email, purpose) so only the most recently sent code ever works —
    otherwise a user who taps "resend" twice could get confused about
    which of two valid codes to use, and old codes would linger as usable
    longer than necessary.

    Deliberately does NOT reveal whether `email` already has an account —
    the response/behavior is identical either way (this function doesn't
    even touch the User table). That's what keeps this endpoint from being
    an email-enumeration oracle.
    """
    email = _normalize_email(email)

    remaining = seconds_until_resend_allowed(email, purpose)
    if remaining > 0:
        raise serializers.ValidationError(
            {"email": f"Please wait {remaining}s before requesting another code."}
        )

    cooldown_key = _cooldown_key(email, purpose)

    # Only one *live* code per (email, purpose) at a time.
    EmailOTP.objects.filter(email=email, purpose=purpose, is_used=False).update(is_used=True)

    code = _generate_code()
    otp = EmailOTP.objects.create(
        email=email,
        purpose=purpose,
        code_hash=_hash_otp(email, code),
        request_ip=request_ip,
        expires_at=timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
    )

    cooldown_expires_at = timezone.now() + timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SECONDS)
    cache.set(cooldown_key, cooldown_expires_at.isoformat(), timeout=settings.OTP_RESEND_COOLDOWN_SECONDS)

    send_otp_email(email, code)
    return otp


def verify_otp(email: str, code: str, *, purpose: str = EmailOTP.Purpose.LOGIN) -> EmailOTP:
    """
    Validates `code` against the latest live OTP for `email`. Raises
    serializers.ValidationError (picked up by core.exceptions'
    custom_exception_handler for a consistent {"error": {...}} response) on
    any failure — expired, wrong code, too many attempts, or never
    requested. Returns the consumed EmailOTP row on success; the caller
    (views.py) is responsible for turning that into a user + tokens.
    """
    email = _normalize_email(email)

    otp = (
        EmailOTP.objects.filter(email=email, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )

    generic_error = {"code": "The code is invalid or has expired. Please request a new one."}

    if otp is None:
        raise serializers.ValidationError(generic_error)

    if otp.expires_at < timezone.now():
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        raise serializers.ValidationError(generic_error)

    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        raise serializers.ValidationError(generic_error)

    # Constant-time comparison — this is a HMAC-style secret check, so we
    # don't want a timing side-channel leaking how many leading digits of
    # the hash matched.
    submitted_hash = _hash_otp(email, code)
    if not hmac.compare_digest(submitted_hash, otp.code_hash):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        remaining = max(settings.OTP_MAX_ATTEMPTS - otp.attempts, 0)
        if remaining == 0:
            otp.is_used = True
            otp.save(update_fields=["is_used"])
            raise serializers.ValidationError(generic_error)
        raise serializers.ValidationError(
            {"code": f"Incorrect code. {remaining} attempt(s) remaining."}
        )

    otp.is_used = True
    otp.consumed_at = timezone.now()
    otp.save(update_fields=["is_used", "consumed_at"])
    return otp


def send_otp_email(email: str, code: str) -> None:
    """
    Synchronous send for MVP scope (matches the 4-week solo-build budget —
    see TRD). This is the one place to swap in `send_otp_email.delay(...)`
    if/when this moves to a Celery task; nothing else in the OTP flow needs
    to change.

    Why that swap matters at scale: right now a slow/hung SMTP call blocks
    the request thread for up to EMAIL_TIMEOUT seconds, and an SMTP outage
    turns "log in" into a 500 for every user simultaneously. The blast
    radius is fine at MVP traffic; it stops being fine once concurrent
    logins are common. Wrapping this call in a Celery task (broker = the
    same Redis already required for caching) decouples "OTP row created"
    from "email actually sent," and retries transient provider failures
    without making the user wait or resubmit.
    """
    context = {"code": code, "expiry_minutes": settings.OTP_EXPIRY_MINUTES}
    text_body = (
        f"Your Gama Diamonds login code is {code}.\n"
        f"It expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n"
        f"If you didn't request this, you can ignore this email."
    )
    try:
        html_body = render_to_string("accounts/otp_email.html", context)
    except Exception:
        html_body = None

    # Always log the OTP in debug for easy dev testing
    if settings.DEBUG:
        print(f"[OTP DEV LOG] OTP code for {email}: {code}")

    send_mail(
        subject="Your Gama Diamonds login code",
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_body,
        fail_silently=False,
    )
