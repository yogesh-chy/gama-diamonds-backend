from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminCartViewSet,
    CartItemDetailView,
    CartItemListCreateView,
    CartView,
    CheckoutView,
    OrderViewSet,
)

app_name = "orders"

router = DefaultRouter()
router.register("admin/carts", AdminCartViewSet, basename="admin-cart")
router.register("", OrderViewSet, basename="order")

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/", CartItemListCreateView.as_view(), name="cart-item-list"),
    path("cart/items/<int:pk>/", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("", include(router.urls)),
]

