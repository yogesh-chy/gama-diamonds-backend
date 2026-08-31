from django.db import migrations


def populate_variants(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    ProductVariant = apps.get_model("products", "ProductVariant")
    ProductSize = apps.get_model("products", "ProductSize")
    CartItem = apps.get_model("orders", "CartItem")
    OrderItem = apps.get_model("orders", "OrderItem")

    for product in Product.objects.all():
        sizes = list(ProductSize.objects.filter(product=product))
        metal_t = product.metal_type or ""
        metal_k = product.metal_karat or ""
        price_val = product.discount_price if (product.discount_price and product.discount_price < product.base_price) else product.base_price
        compare_val = product.base_price if (product.discount_price and product.discount_price < product.base_price) else None

        if sizes:
            for idx, sz in enumerate(sizes):
                sku_str = f"{product.sku}-{sz.size.replace(' ', '')}"
                if ProductVariant.objects.filter(sku=sku_str).exists():
                    sku_str = f"{sku_str}-{idx+1}"
                variant, _ = ProductVariant.objects.get_or_create(
                    product=product,
                    metal_type=metal_t,
                    metal_karat=metal_k,
                    size=sz.size,
                    defaults={
                        "sku": sku_str,
                        "price": price_val,
                        "compare_at_price": compare_val,
                        "stock": sz.stock,
                        "is_default": (idx == 0),
                        "is_active": product.is_active,
                    }
                )
        else:
            sku_str = product.sku
            if ProductVariant.objects.filter(sku=sku_str).exists():
                sku_str = f"{sku_str}-DEF"
            variant, _ = ProductVariant.objects.get_or_create(
                product=product,
                metal_type=metal_t,
                metal_karat=metal_k,
                size="",
                defaults={
                    "sku": sku_str,
                    "price": price_val,
                    "compare_at_price": compare_val,
                    "stock": product.total_stock,
                    "is_default": True,
                    "is_active": product.is_active,
                }
            )

    # Link existing CartItems
    for item in CartItem.objects.filter(variant__isnull=True):
        if item.size:
            var = ProductVariant.objects.filter(product_id=item.product_id, size=item.size).first()
        else:
            var = None
        if not var:
            var = ProductVariant.objects.filter(product_id=item.product_id).first()
        if var:
            item.variant = var
            item.save(update_fields=["variant"])

    # Link existing OrderItems
    for item in OrderItem.objects.filter(variant__isnull=True, product__isnull=False):
        if item.size:
            var = ProductVariant.objects.filter(product_id=item.product_id, size=item.size).first()
        else:
            var = None
        if not var:
            var = ProductVariant.objects.filter(product_id=item.product_id).first()
        if var:
            item.variant = var
            item.metal_type = var.metal_type
            item.metal_karat = var.metal_karat
            item.save(update_fields=["variant", "metal_type", "metal_karat"])


def reverse_populate(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0004_product_seo_description_product_seo_keywords_and_more"),
        ("orders", "0005_alter_cartitem_unique_together_cartitem_variant_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_variants, reverse_code=reverse_populate),
    ]
