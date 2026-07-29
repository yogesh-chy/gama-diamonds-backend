from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import Address
from products.models import Product, ProductSize

from .models import Cart, CartItem, Order, OrderItem


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _reserved_quantity(product_id, size=""):
    """Quantity of this product+size currently held by OTHER pending,
    unexpired checkouts — subtracted from real stock to get what's
    actually available to a new checkout right now."""
    return (
        OrderItem.objects.filter(
            product_id=product_id,
            size=size,
            order__status="pending_payment",
            order__reservation_expires_at__gt=timezone.now(),
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )


def validate_stock(product, quantity, size=""):
    if size:
        product_size = product.sizes.filter(size=size).first()
        if product_size is None:
            raise ValidationError({"size": f"'{size}' is not a valid size for this product."})
        available = product_size.stock
    else:
        if product.sizes.exists():
            raise ValidationError({"size": "This product requires a size to be selected."})
        available = product.total_stock

    effective_available = available - _reserved_quantity(product.id, size)

    if quantity > effective_available:
        raise ValidationError(
            {"quantity": f"Only {max(effective_available, 0)} unit(s) available for this selection."}
        )


@transaction.atomic
def add_item_to_cart(cart, product, quantity, size=""):
    if not product.is_active:
        raise ValidationError({"product": "This product is not currently available."})

    existing = CartItem.objects.select_for_update().filter(cart=cart, product=product, size=size).first()
    new_quantity = (existing.quantity if existing else 0) + quantity
    validate_stock(product, new_quantity, size)

    if existing:
        existing.quantity = new_quantity
        existing.save(update_fields=["quantity", "updated_at"])
        return existing

    return CartItem.objects.create(cart=cart, product=product, size=size, quantity=quantity)


@transaction.atomic
def update_cart_item_quantity(cart_item, quantity):
    validate_stock(cart_item.product, quantity, cart_item.size)
    cart_item.quantity = quantity
    cart_item.save(update_fields=["quantity", "updated_at"])
    return cart_item


def snapshot_order_items(order, cart_items):
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product=item.product,
            product_name=item.product.name,
            product_sku=item.product.sku,
            product_price=item.unit_price,
            size=item.size,
            quantity=item.quantity,
        )
        for item in cart_items
    ])


@transaction.atomic
def checkout_cart(user, address_id):
    """
    Creates a pending_payment Order (with a time-boxed stock reservation)
    snapshotting the cart's current contents and the chosen address, then
    empties the cart. Does NOT touch real stock or talk to Razorpay — the
    view layer creates the Razorpay order on top of what this returns.
    """
    cart = get_or_create_cart(user)
    cart_items = list(cart.items.select_related("product").select_for_update(of=("self",)))

    if not cart_items:
        raise ValidationError({"cart": "Your cart is empty."})

    try:
        address = Address.objects.get(pk=address_id, user=user)
    except Address.DoesNotExist:
        raise ValidationError({"address_id": "Address not found for this account."})

    # Lock the actual product/size rows before checking availability. This
    # is what actually closes the "two users both buy the last unit" race:
    # whichever checkout gets here first holds the row lock until it
    # commits, so the second checkout's _reserved_quantity() count (once
    # unblocked) is guaranteed to already include the first checkout's
    # just-created reservation.
    for item in cart_items:
        if item.size:
            ProductSize.objects.select_for_update().filter(
                product_id=item.product_id, size=item.size
            ).first()
        else:
            Product.objects.select_for_update().filter(pk=item.product_id).first()

    for item in cart_items:
        validate_stock(item.product, item.quantity, item.size)

    subtotal = sum((item.line_total for item in cart_items), Decimal("0.00"))
    tax_amount = sum(
        (item.line_total * (item.product.tax_percentage / Decimal("100")) for item in cart_items),
        Decimal("0.00"),
    )
    total_amount = subtotal + tax_amount

    order = Order.objects.create(
        user=user,
        address_full_name=address.full_name,
        address_phone_number=address.phone_number,
        address_street=address.street_address,
        address_city=address.city,
        address_state=address.state,
        address_postal_code=address.postal_code,
        address_country=address.country,
        status="pending_payment",
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        reservation_expires_at=timezone.now() + timedelta(minutes=settings.CHECKOUT_RESERVATION_MINUTES),
    )
    snapshot_order_items(order, cart_items)
    cart.items.all().delete()

    return order


@transaction.atomic
def decrement_stock_for_order(order):
    """
    Decrements real stock for every line item on an order, exactly once.
    Guarded by Order.stock_decremented_at so this is a safe no-op if
    called twice for the same order (/verify/ and the webhook can both
    race to confirm the same payment).
    """
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.stock_decremented_at is not None:
        return

    for item in order.items.select_related("product"):
        if item.product is None:
            continue  # product was deleted after the order was placed
        if item.size:
            product_size = item.product.sizes.filter(size=item.size).first()
            if product_size:
                product_size.stock = max(product_size.stock - item.quantity, 0)
                product_size.save(update_fields=["stock"])
        else:
            item.product.total_stock = max(item.product.total_stock - item.quantity, 0)
            item.product.save(update_fields=["total_stock"])

    order.stock_decremented_at = timezone.now()
    order.save(update_fields=["stock_decremented_at"])
