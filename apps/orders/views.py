import logging

from django.conf import settings
from django.http import Http404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response

from payments.razorpay_client import create_razorpay_order

from . import services
from .models import CartItem, Order
from .serializers import (
    AddCartItemSerializer,
    CartSerializer,
    CheckoutSerializer,
    OrderSerializer,
    UpdateCartItemSerializer,
)

logger = logging.getLogger(__name__)


class CartView(generics.RetrieveAPIView):
    """GET /api/orders/cart/ — the current user's cart (created lazily)."""
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return services.get_or_create_cart(self.request.user)


class CartItemListCreateView(generics.GenericAPIView):
    """POST /api/orders/cart/items/ — add an item to the current user's cart."""
    serializer_class = AddCartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = services.get_or_create_cart(request.user)
        services.add_item_to_cart(cart, **serializer.validated_data)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(generics.GenericAPIView):
    """PATCH/DELETE /api/orders/cart/items/{id}/ — update quantity or remove."""
    serializer_class = UpdateCartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, pk):
        try:
            item = CartItem.objects.select_related("cart").get(pk=pk)
        except CartItem.DoesNotExist:
            raise Http404()
        if item.cart.user_id != request.user.id:
            raise Http404()
        return item

    def patch(self, request, pk):
        item = self.get_object(request, pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.update_cart_item_quantity(item, serializer.validated_data["quantity"])
        return Response(CartSerializer(item.cart).data)

    def delete(self, request, pk):
        item = self.get_object(request, pk)
        cart = item.cart
        item.delete()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CheckoutView(generics.GenericAPIView):
    """
    POST /api/orders/checkout/ — creates an Order (status=pending_payment)
    from the current cart + the given address, empties the cart, then
    creates a matching Razorpay Order and returns what the frontend needs
    to open the Razorpay Checkout widget (TRD Section 6, step 1).

    orders/services.py deliberately never imports payments/ — this view
    is the one seam where the two apps meet, keeping "no app talks to
    Razorpay except payments/" true at the service-layer boundary.
    """
    serializer_class = CheckoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.checkout_cart(request.user, serializer.validated_data["address_id"])

        try:
            razorpay_order = create_razorpay_order(order)
        except Exception:
            # The Order already exists as pending_payment with no
            # razorpay_order_id yet — nothing is lost. Logged so an
            # operator can see Razorpay outages; a "retry checkout" flow
            # on the frontend can re-attempt against the same order_id
            # rather than re-validating the (now-empty) cart from scratch.
            logger.exception("Razorpay order creation failed for Order #%s", order.id)
            return Response(
                {"detail": "Payment gateway is temporarily unavailable. Your order was saved — please try again shortly."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "order": OrderSerializer(order).data,
                "razorpay": {
                    "razorpay_order_id": razorpay_order["id"],
                    "amount": razorpay_order["amount"],
                    "currency": razorpay_order["currency"],
                    "key_id": settings.RAZORPAY_KEY_ID,
                },
            },
            status=status.HTTP_201_CREATED,
        )


from core.permissions import IsAdminUser
from django.db.models import Q
from .models import Cart, CartItem, Order
from .serializers import (
    AddCartItemSerializer,
    AdminCartSerializer,
    CartSerializer,
    CheckoutSerializer,
    OrderSerializer,
    UpdateCartItemSerializer,
)


class OrderViewSet(viewsets.ModelViewSet):
    """
    GET /api/orders/ and /api/orders/{id}/ — shopper's own history or all orders for staff.
    PATCH /api/orders/{id}/ — status transitions by staff.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            qs = Order.objects.all().prefetch_related("items").select_related("user")
            status_param = self.request.query_params.get("status")
            if status_param:
                qs = qs.filter(status__iexact=status_param)
            search = self.request.query_params.get("search")
            if search:
                qs = qs.filter(
                    Q(id__icontains=search) |
                    Q(user__email__icontains=search) |
                    Q(address_full_name__icontains=search) |
                    Q(razorpay_order_id__icontains=search)
                )
            return qs
        return Order.objects.filter(user=user).prefetch_related("items")


class AdminCartViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/orders/admin/carts/ — lists all customer shopping carts for staff.
    """
    serializer_class = AdminCartSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = Cart.objects.prefetch_related("items__product__images", "items__product", "user").all()

    def get_queryset(self):
        qs = super().get_queryset()
        # Filter out empty carts by default or support search
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(user__email__icontains=search)
        return qs

