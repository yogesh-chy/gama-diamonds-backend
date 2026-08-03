from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AddressViewSet,
    AdminLoginView,
    AdminUserViewSet,
    LogoutView,
    MeView,
    RequestOTPView,
    VerifyOTPView,
)

app_name = "accounts"

router = DefaultRouter()
router.register("admin/users", AdminUserViewSet, basename="admin-user")
router.register("addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("otp/request/", RequestOTPView.as_view(), name="otp_request"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp_verify"),
    path("admin/login/", AdminLoginView.as_view(), name="admin_login"),

    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]

