from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_razorpay_order():
    """
    Every checkout test goes through orders.views.create_razorpay_order,
    which calls the real Razorpay SDK. Per the TRD's own testing plan
    (Section 8), tests never hit the live Razorpay API — this stands in a
    fake response shaped like what the SDK actually returns.
    """
    with patch("orders.views.create_razorpay_order") as mock_create:
        mock_create.side_effect = lambda order: {
            "id": f"order_fake_{order.id}",
            "amount": int(order.total_amount * 100),
            "currency": "INR",
        }
        yield mock_create
