from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AddressViewSet,
    LogoutView,
    MeView,
    RequestOTPView,
    VerifyOTPView,
)

app_name = "accounts"

router = DefaultRouter()
router.register("addresses", AddressViewSet, basename="address")

urlpatterns = [
    # OTP login/signup — replaces the old password-based /register/ and
    # /login/ endpoints entirely (see accounts/services.py, accounts/views.py).
    path("otp/request/", RequestOTPView.as_view(), name="otp_request"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp_verify"),

    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
