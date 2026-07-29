from rest_framework.throttling import SimpleRateThrottle


class _ScopedIPThrottle(SimpleRateThrottle):
    """Per-IP limiter, keyed the standard DRF way. Subclasses just set `scope`."""

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class OTPRequestThrottle(_ScopedIPThrottle):
    """
    Coarse per-IP ceiling on POST /otp/request/ (rate: DEFAULT_THROTTLE_RATES
    ["otp_request"]). Stops one IP from spraying OTP-request calls across
    many different email addresses (which OTPRequestEmailThrottle alone
    wouldn't catch, since that one keys by email).
    """
    scope = "otp_request"


class OTPRequestEmailThrottle(SimpleRateThrottle):
    """
    Per-*email* ceiling on POST /otp/request/, independent of source IP.
    This is the one that actually protects a specific inbox from being
    spammed with codes (and protects the email-provider bill/reputation)
    even if the caller rotates IPs. Silently no-ops (never throttles) when
    the request doesn't carry a usable email, since request-shape
    validation is the serializer's job, not the throttle's — an
    unthrottled malformed request will just fail validation right after.
    """
    scope = "otp_request_email"

    def get_cache_key(self, request, view):
        email = (request.data or {}).get("email")
        if not email or not isinstance(email, str):
            return None
        ident = email.strip().lower()
        return self.cache_format % {"scope": self.scope, "ident": ident}


class OTPVerifyThrottle(_ScopedIPThrottle):
    """
    Per-IP limiter on POST /otp/verify/. Deliberately loose — the real
    anti-brute-force control on guessing a code is the per-OTP attempts
    counter in accounts/services.py (OTP_MAX_ATTEMPTS), which kills a
    single code after N wrong guesses regardless of IP. This throttle just
    caps how fast one IP can churn through *different* OTP records.
    """
    scope = "otp_verify"
