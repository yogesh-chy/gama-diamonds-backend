from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "product_sku", "product_price", "size", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_amount", "stock_decremented_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__email", "razorpay_order_id", "razorpay_payment_id")
    readonly_fields = (
        "user", "subtotal", "tax_amount", "total_amount",
        "address_full_name", "address_phone_number", "address_street",
        "address_city", "address_state", "address_postal_code", "address_country",
        "razorpay_order_id", "razorpay_payment_id", "reservation_expires_at", "stock_decremented_at",
        "created_at", "updated_at",
    )
    inlines = [OrderItemInline]

    fieldsets = (
        (None, {"fields": ("user", "status")}),
        ("Totals", {"fields": ("subtotal", "tax_amount", "total_amount")}),
        (
            "Shipping address (snapshot)",
            {
                "fields": (
                    "address_full_name", "address_phone_number", "address_street",
                    "address_city", "address_state", "address_postal_code", "address_country",
                )
            },
        ),
        ("Payment", {"fields": ("razorpay_order_id", "razorpay_payment_id", "reservation_expires_at", "stock_decremented_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("product", "size", "quantity")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "total_items", "total_amount", "updated_at")
    search_fields = ("user__email",)
    inlines = [CartItemInline]
