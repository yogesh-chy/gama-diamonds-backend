from django.conf import settings
from django.urls import path

from .views import RazorpayWebhookView, VerifyPaymentView

app_name = "payments"

urlpatterns = [
    path("verify/", VerifyPaymentView.as_view(), name="verify"),
    path("webhook/", RazorpayWebhookView.as_view(), name="webhook"),
]

if settings.DEBUG:
    # Manual smoke-test page — never present when DEBUG=False, so this
    # never accidentally ships to production.
    from .views import TestCheckoutPageView

    urlpatterns += [
        path("test-checkout/", TestCheckoutPageView.as_view(), name="test-checkout"),
    ]
