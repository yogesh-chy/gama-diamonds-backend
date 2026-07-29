"""
HMAC signature verification — the actual source of truth for "did this
payment happen". Never trust the frontend's success callback on its own
(TRD Section 6, step 5).
"""
import hashlib
import hmac

from django.conf import settings


def verify_checkout_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """
    Recomputes the signature Razorpay returns to the frontend after a
    successful checkout (order_id|payment_id, HMAC-SHA256 with the API key
    secret) and compares it to what the frontend submitted to /verify/.
    """
    payload = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
    expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature or "")


def verify_webhook_signature(raw_body: bytes, received_signature: str) -> bool:
    """
    Verifies a Razorpay webhook payload using a SEPARATE secret from
    /verify/'s (the webhook secret, configured in the Razorpay dashboard,
    not the API key secret) — TRD Section 6, step 8, two different
    secrets on purpose so a leaked key secret alone can't forge webhooks.
    """
    expected = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received_signature or "")
