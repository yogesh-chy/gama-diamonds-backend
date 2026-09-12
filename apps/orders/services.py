from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import Address
from products.models import Product, ProductSize, ProductVariant

from .models import Cart, CartItem, Order, OrderItem


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _reserved_quantity(product_id=None, size="", variant_id=None):
    """Quantity of this variant or product+size currently held by OTHER pending,
    unexpired checkouts — subtracted from real stock to get what's
    actually available to a new checkout right now."""
    if variant_id:
        return (
            OrderItem.objects.filter(
                variant_id=variant_id,
                order__status="pending_payment",
                order__reservation_expires_at__gt=timezone.now(),
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

    return (
        OrderItem.objects.filter(
            product_id=product_id,
            size=size,
            order__status="pending_payment",
            order__reservation_expires_at__gt=timezone.now(),
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )


def validate_stock(product=None, quantity=1, size="", variant=None):
    if variant:
        available = variant.stock
        reserved = _reserved_quantity(variant_id=variant.id)
        effective_available = available - reserved
        if quantity > effective_available:
            raise ValidationError(
                {"quantity": f"Only {max(effective_available, 0)} unit(s) available for this selection."}
            )
        return

    if product:
        if product.sizes.exists():
            product_size = product.sizes.filter(size=size).first() if size else None
            if product_size is None:
                product_size = product.sizes.first()
            available = product_size.stock if product_size else 0
            size = product_size.size if product_size else size
        else:
            available = product.total_stock

        effective_available = available - _reserved_quantity(product_id=product.id, size=size)

        if quantity > effective_available:
            raise ValidationError(
                {"quantity": f"Only {max(effective_available, 0)} unit(s) available for this selection."}
            )


@transaction.atomic
def add_item_to_cart(cart, product=None, quantity=1, size="", variant_id=None, variant=None):
    if not variant and variant_id:
        try:
            variant = ProductVariant.objects.get(pk=variant_id)
        except ProductVariant.DoesNotExist:
            raise ValidationError({"variant_id": "Specified product variant does not exist."})
    elif not variant and product:
        has_sized_variants = product.variants.filter(is_active=True).exclude(size="").exists()
        if (has_sized_variants or product.sizes.exists()) and not size:
            raise ValidationError({"size": "Size is required for this product."})

        if size:
            variant = product.variants.filter(size__iexact=size, is_active=True).first()
        if not variant and not has_sized_variants:
            variant = product.variants.filter(is_active=True, is_default=True).first() or product.variants.filter(is_active=True).first()

    if variant:
        product = variant.product
        if not variant.is_active or not product.is_active:
            raise ValidationError({"product": "This product variant is not currently available."})
        
        existing = CartItem.objects.select_for_update().filter(cart=cart, variant=variant).first()
        new_quantity = (existing.quantity if existing else 0) + quantity
        validate_stock(quantity=new_quantity, variant=variant)

        if existing:
            existing.quantity = new_quantity
            existing.save(update_fields=["quantity", "updated_at"])
            return existing

        return CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant,
            size=variant.size or size,
            quantity=quantity
        )

    if not product.is_active:
        raise ValidationError({"product": "This product is not currently available."})

    existing = CartItem.objects.select_for_update().filter(cart=cart, product=product, size=size).first()
    new_quantity = (existing.quantity if existing else 0) + quantity
    validate_stock(product=product, quantity=new_quantity, size=size)

    if existing:
        existing.quantity = new_quantity
        existing.save(update_fields=["quantity", "updated_at"])
        return existing

    return CartItem.objects.create(cart=cart, product=product, size=size, quantity=quantity)


@transaction.atomic
def update_cart_item_quantity(cart_item, quantity):
    if cart_item.variant:
        validate_stock(quantity=quantity, variant=cart_item.variant)
    else:
        validate_stock(product=cart_item.product, quantity=quantity, size=cart_item.size)

    cart_item.quantity = quantity
    cart_item.save(update_fields=["quantity", "updated_at"])
    return cart_item


def snapshot_order_items(order, cart_items):
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product=item.product,
            variant=item.variant,
            product_name=item.product.name,
            product_sku=item.variant.sku if item.variant else item.product.sku,
            product_price=item.unit_price,
            metal_type=item.variant.metal_type if item.variant else getattr(item.product, "metal_type", "") or "",
            metal_karat=item.variant.metal_karat if item.variant else getattr(item.product, "metal_karat", "") or "",
            size=item.variant.size if item.variant else item.size,
            quantity=item.quantity,
        )
        for item in cart_items
    ])


@transaction.atomic
def checkout_cart(user, address_id):
    cart = get_or_create_cart(user)
    cart_items = list(cart.items.select_related("product", "variant").select_for_update(of=("self",)))

    if not cart_items:
        raise ValidationError({"cart": "Your cart is empty."})

    try:
        address = Address.objects.get(pk=address_id, user=user)
    except Address.DoesNotExist:
        raise ValidationError({"address_id": "Address not found for this account."})

    for item in cart_items:
        if item.variant:
            ProductVariant.objects.select_for_update().filter(pk=item.variant_id).first()
        elif item.size:
            ProductSize.objects.select_for_update().filter(
                product_id=item.product_id, size=item.size
            ).first()
        else:
            Product.objects.select_for_update().filter(pk=item.product_id).first()

    for item in cart_items:
        if item.variant:
            validate_stock(quantity=item.quantity, variant=item.variant)
        else:
            validate_stock(product=item.product, quantity=item.quantity, size=item.size)

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
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.stock_decremented_at is not None:
        return

    for item in order.items.select_related("product", "variant"):
        if item.variant:
            item.variant.stock = max(item.variant.stock - item.quantity, 0)
            item.variant.save(update_fields=["stock"])
            if item.product:
                item.product.total_stock = sum(v.stock for v in item.product.variants.filter(is_active=True))
                item.product.save(update_fields=["total_stock"])
        elif item.product:
            if item.size:
                product_size = item.product.sizes.filter(size=item.size).first()
                if product_size:
                    product_size.stock = max(product_size.stock - item.quantity, 0)
                    product_size.save(update_fields=["stock"])
            item.product.total_stock = max(item.product.total_stock - item.quantity, 0)
            item.product.save(update_fields=["total_stock"])

    order.stock_decremented_at = timezone.now()
    order.save(update_fields=["stock_decremented_at"])

