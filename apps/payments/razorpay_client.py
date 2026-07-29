"""
Thin wrapper around the Razorpay SDK. This is the ONLY module in the
project allowed to talk to Razorpay directly — orders/ only knows
"checkout produced a pending order" and calls create_razorpay_order() on
it, keeping the payment provider swappable later without touching
orders/services.py (TRD Section 3 design note).
"""
import razorpay
from django.conf import settings


def get_client():
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(order):
    """
    Creates a Razorpay Order matching our already-created (pending_payment)
    Order and stores the returned id on it.

    Amount is converted to paise (Razorpay's smallest currency unit) —
    this is a common integration bug: passing rupees directly silently
    undercharges by 100x.
    """
    client = get_client()
    amount_in_paise = int(order.total_amount * 100)

    razorpay_order = client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"order_{order.id}",
        "payment_capture": 1,
    })

    order.razorpay_order_id = razorpay_order["id"]
    order.save(update_fields=["razorpay_order_id"])
    return razorpay_order
