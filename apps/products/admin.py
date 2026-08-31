from django.contrib import admin

from .models import (
    Brand,
    Category,
    Collection,
    DiamondSpecification,
    DiamondType,
    Product,
    ProductImage,
    ProductSize,
    ProductVariant,
    Style,
    Subcategory,
)


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    inlines = [SubcategoryInline]


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug")
    list_filter = ("category",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(DiamondType)
class DiamondTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("sku", "metal_type", "metal_karat", "size", "length", "bangle_size", "price", "compare_at_price", "cost_price", "stock", "is_active", "is_default")


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 0


class DiamondSpecificationInline(admin.StackedInline):
    model = DiamondSpecification
    extra = 0
    max_num = 1


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "metal_type", "metal_karat", "size", "length", "bangle_size", "price", "stock", "is_active", "is_default")
    list_filter = ("metal_type", "metal_karat", "is_active", "is_default")
    search_fields = ("sku", "product__name", "size", "length", "bangle_size")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "sku", "category", "diamond_type", "brand", "base_price",
        "discount_price", "total_stock", "is_active", "is_featured", "created_at",
    )
    list_filter = ("category", "metal_type", "diamond_type", "brand", "is_active", "is_featured", "gender")
    search_fields = ("name", "sku", "slug", "product_code", "internal_reference", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("sku", "created_at", "updated_at")
    filter_horizontal = ("styles", "collections", "related_products")
    inlines = [DiamondSpecificationInline, ProductImageInline, ProductVariantInline, ProductSizeInline]
    list_editable = ("total_stock", "is_active")

    fieldsets = (
        ("Basic Information", {"fields": ("name", "slug", "sku", "product_code", "internal_reference", "description")}),
        (
            "Categorization & Navigation",
            {
                "fields": (
                    "category", "category_ref", "subcategory_ref",
                    "diamond_type", "brand", "collections", "styles",
                    "gender", "occasion",
                )
            },
        ),
        ("Pricing & Tax", {"fields": ("base_price", "discount_price", "tax_percentage")}),
        ("Inventory Control", {"fields": ("total_stock", "low_stock_threshold")}),
        (
            "Ring Specifications",
            {
                "classes": ("collapse",),
                "fields": (
                    "ring_type", "ring_style", "ring_shape", "band_style",
                    "band_fit", "band_width", "ring_profile", "ring_finish",
                    "ring_thickness", "resizable",
                ),
            },
        ),
        (
            "Earring Specifications",
            {
                "classes": ("collapse",),
                "fields": (
                    "earring_type", "earring_style", "closure_type",
                    "drop_length", "earring_width", "earring_height",
                ),
            },
        ),
        (
            "Necklace & Pendant Specifications",
            {
                "classes": ("collapse",),
                "fields": (
                    "necklace_type", "necklace_style", "chain_type", "chain_length",
                    "pendant_included", "pendant_type", "pendant_shape", "pendant_height",
                    "pendant_width", "pendant_depth", "chain_included", "clasp_type",
                ),
            },
        ),
        (
            "Bracelet & Bangle Specifications",
            {
                "classes": ("collapse",),
                "fields": (
                    "bracelet_type", "bracelet_style", "bracelet_length", "bracelet_width",
                    "bracelet_thickness", "bangle_type", "inner_diameter", "bangle_width",
                    "bangle_thickness", "opening_type", "bangle_size", "adjustable",
                ),
            },
        ),
        (
            "Gemstone Specifications",
            {
                "classes": ("collapse",),
                "fields": (
                    "gemstone_included", "gemstone_type", "gemstone_shape", "gemstone_colour",
                    "gemstone_carat_weight", "gemstone_count", "gemstone_origin",
                ),
            },
        ),
        (
            "Dimensions & Weight",
            {
                "classes": ("collapse",),
                "fields": ("height", "width", "length", "depth", "thickness", "weight"),
            },
        ),
        (
            "Customisation & Delivery",
            {
                "fields": (
                    "finish", "customisation_available", "engraving_available",
                    "engraving_character_limit", "engraving_instructions", "personalisation_available",
                    "delivery_type", "estimated_delivery_time", "next_day_delivery_available",
                    "made_to_order", "production_time", "shipping_weight",
                )
            },
        ),
        (
            "SEO & OpenGraph",
            {
                "fields": (
                    "seo_title", "seo_description", "seo_keywords",
                    "canonical_url", "og_title", "og_description", "og_image",
                )
            },
        ),
        ("Related Products", {"fields": ("related_products",)}),
        ("Status & Feature Flags", {"fields": ("is_active", "is_featured")}),
        ("System Timestamps", {"fields": ("created_at", "updated_at")}),
    )

