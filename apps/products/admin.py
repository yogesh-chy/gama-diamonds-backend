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


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1


class DiamondSpecificationInline(admin.StackedInline):
    model = DiamondSpecification
    extra = 0
    max_num = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "sku", "category", "diamond_type", "brand", "base_price",
        "discount_price", "total_stock", "is_active", "is_featured", "created_at",
    )
    list_filter = ("category", "metal_type", "diamond_type", "brand", "is_active", "is_featured", "gender")
    search_fields = ("name", "sku", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("sku", "created_at", "updated_at")
    filter_horizontal = ("styles", "collections")
    inlines = [DiamondSpecificationInline, ProductImageInline, ProductSizeInline]
    list_editable = ("total_stock", "is_active")

    fieldsets = (
        (None, {"fields": ("name", "slug", "sku", "description")}),
        (
            "Categorization",
            {
                "fields": (
                    "category", "category_ref", "subcategory_ref",
                    "diamond_type", "brand", "collections", "styles",
                    "gender", "occasion",
                )
            },
        ),
        ("Pricing", {"fields": ("base_price", "discount_price", "tax_percentage")}),
        ("Inventory", {"fields": ("total_stock", "low_stock_threshold")}),
        (
            "Attributes",
            {
                "fields": (
                    "metal_type", "metal_karat", "diamond_cut",
                    "earring_type", "necklace_style", "bracelet_type",
                    "band_fit", "finish", "customisation_available", "engraving_available",
                )
            },
        ),
        ("Status", {"fields": ("is_active", "is_featured")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
