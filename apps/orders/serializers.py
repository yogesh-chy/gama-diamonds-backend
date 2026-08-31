from rest_framework import serializers

from products.models import Product, ProductVariant

from .models import Cart, CartItem, Order, OrderItem


class CartItemProductSummarySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "sku", "image_url", "is_active")

    def get_image_url(self, obj):
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()
        return primary.url if primary else None


class CartItemVariantSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ("id", "sku", "metal_type", "metal_karat", "size", "price", "stock")


class CartItemSerializer(serializers.ModelSerializer):
    product_detail = CartItemProductSummarySerializer(source="product", read_only=True)
    variant_detail = CartItemVariantSummarySerializer(source="variant", read_only=True)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "product_detail", "variant", "variant_detail", "size", "quantity", "unit_price", "line_total")
        extra_kwargs = {"product": {"write_only": True}, "variant": {"write_only": True}}


class AddCartItemSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source="product", required=False, allow_null=True)
    variant_id = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), source="variant", required=False, allow_null=True)
    size = serializers.CharField(required=False, allow_blank=True, default="")
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        if not attrs.get("product") and not attrs.get("variant"):
            raise serializers.ValidationError("Either product_id or variant_id must be provided.")
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "items", "total_amount", "total_items", "updated_at")


class AdminCartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "user_id", "user_email", "items", "total_amount", "total_items", "created_at", "updated_at")


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "variant", "product_name", "product_sku", "product_price", "metal_type", "metal_karat", "size", "quantity", "line_total")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "user_id", "user_email", "status", "subtotal", "tax_amount", "total_amount",
            "address_full_name", "address_phone_number", "address_street",
            "address_city", "address_state", "address_postal_code", "address_country",
            "razorpay_order_id", "reservation_expires_at", "items", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "user_id", "user_email", "subtotal", "tax_amount", "total_amount",
            "address_full_name", "address_phone_number", "address_street",
            "address_city", "address_state", "address_postal_code", "address_country",
            "razorpay_order_id", "reservation_expires_at", "items", "created_at", "updated_at",
        )

