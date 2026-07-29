from decimal import Decimal

from django.conf import settings
from django.db import models

from products.models import Product


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="cart", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart({self.user.email})"

    @property
    def total_amount(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_items", on_delete=models.CASCADE)
    # Optional — only relevant for products seeded with ProductSize rows (rings, etc).
    size = models.CharField(max_length=50, blank=True, default="")
    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cart", "product", "size")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.cart.user.email})"

    @property
    def unit_price(self):
        return Decimal(str(self.product.price))

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def available_stock(self):
        if self.size:
            product_size = self.product.sizes.filter(size=self.size).first()
            return product_size.stock if product_size else 0
        return self.product.total_stock


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending_payment", "Pending Payment"),
        ("expired", "Expired (Reservation Lapsed)"),
        ("payment_failed", "Payment Failed"),
        ("paid", "Paid"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE)

    address_full_name = models.CharField(max_length=255)
    address_phone_number = models.CharField(max_length=16)
    address_street = models.CharField(max_length=255)
    address_city = models.CharField(max_length=100)
    address_state = models.CharField(max_length=100)
    address_postal_code = models.CharField(max_length=20)
    address_country = models.CharField(max_length=100)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_payment")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    razorpay_order_id = models.CharField(max_length=100, blank=True, default="", db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, default="")

    # A pending checkout temporarily holds stock while the customer completes
    # Razorpay Checkout. Late verified payments are still honored.
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    stock_decremented_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.user.email} — {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.SET_NULL, null=True)

    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50)
    product_price = models.DecimalField(max_digits=12, decimal_places=2)
    size = models.CharField(max_length=50, blank=True, default="")
    quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def line_total(self):
        return self.product_price * self.quantity
