from rest_framework import serializers
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


class ProductImageSerializer(serializers.ModelSerializer):
    publicId = serializers.CharField(source="public_id", required=False, allow_blank=True)
    isPrimary = serializers.BooleanField(source="is_primary", required=False, default=False)

    class Meta:
        model = ProductImage
        fields = ["id", "url", "publicId", "isPrimary"]


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", "size", "stock"]


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ["id", "name", "slug"]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "subcategories"]


class StyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Style
        fields = ["id", "name", "slug"]


class DiamondTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiamondType
        fields = ["id", "name", "slug"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug"]


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "name", "slug", "description"]


class DiamondSpecificationSerializer(serializers.ModelSerializer):
    caratWeight = serializers.DecimalField(source="carat_weight", max_digits=6, decimal_places=2, required=False)
    sideCaratWeight = serializers.DecimalField(source="side_carat_weight", max_digits=6, decimal_places=2, required=False, allow_null=True)
    cutGrade = serializers.CharField(source="cut_grade", required=False, allow_null=True, allow_blank=True)
    colourGrade = serializers.CharField(source="colour_grade", required=False, allow_null=True, allow_blank=True)
    clarityGrade = serializers.CharField(source="clarity_grade", required=False, allow_null=True, allow_blank=True)
    certificationLab = serializers.CharField(source="certification_lab", required=False)
    certificateNumber = serializers.CharField(source="certificate_number", required=False, allow_blank=True)

    class Meta:
        model = DiamondSpecification
        fields = [
            "carat_weight", "caratWeight",
            "side_carat_weight", "sideCaratWeight",
            "cut_grade", "cutGrade",
            "colour_grade", "colourGrade",
            "clarity_grade", "clarityGrade",
            "certification_lab", "certificationLab",
            "certificate_number", "certificateNumber",
        ]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False)
    sizes = ProductSizeSerializer(many=True, required=False)
    diamond_spec = DiamondSpecificationSerializer(required=False, allow_null=True)

    # Cross-cutting facets — read as nested objects, write as id lists/ids
    # (standard DRF PrimaryKeyRelatedField — no manual parsing needed,
    # unlike images/sizes which are nested objects created on the fly).
    styles = serializers.PrimaryKeyRelatedField(many=True, queryset=Style.objects.all(), required=False)
    stylesDetail = StyleSerializer(source="styles", many=True, read_only=True)
    collections = serializers.PrimaryKeyRelatedField(many=True, queryset=Collection.objects.all(), required=False)
    collectionsDetail = CollectionSerializer(source="collections", many=True, read_only=True)
    diamond_type = serializers.PrimaryKeyRelatedField(queryset=DiamondType.objects.all(), required=False, allow_null=True)
    diamondTypeDetail = DiamondTypeSerializer(source="diamond_type", read_only=True)
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), required=False, allow_null=True)
    brandDetail = BrandSerializer(source="brand", read_only=True)

    # Alias camelCase fields for Next.js frontend compatibility
    basePrice = serializers.DecimalField(source="base_price", max_digits=12, decimal_places=2, required=False)
    discountPrice = serializers.DecimalField(source="discount_price", max_digits=12, decimal_places=2, required=False, allow_null=True)
    totalStock = serializers.IntegerField(source="total_stock", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)
    isFeatured = serializers.BooleanField(source="is_featured", required=False)
    diamondCut = serializers.CharField(source="diamond_cut", required=False, allow_null=True, allow_blank=True)
    metalType = serializers.CharField(source="metal_type", required=False, allow_null=True, allow_blank=True)
    metalKarat = serializers.CharField(source="metal_karat", required=False, allow_null=True, allow_blank=True)
    earringType = serializers.CharField(source="earring_type", required=False, allow_null=True, allow_blank=True)
    necklaceStyle = serializers.CharField(source="necklace_style", required=False, allow_null=True, allow_blank=True)
    braceletType = serializers.CharField(source="bracelet_type", required=False, allow_null=True, allow_blank=True)
    bandFit = serializers.CharField(source="band_fit", required=False, allow_null=True, allow_blank=True)
    customisationAvailable = serializers.CharField(source="customisation_available", required=False)
    engravingAvailable = serializers.CharField(source="engraving_available", required=False)

    # Structural pricing and inventory helpers for legacy frontend components
    pricing = serializers.SerializerMethodField()
    inventory = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "description",
            "category",
            "base_price",
            "discount_price",
            "basePrice",
            "discountPrice",
            "pricing",
            "total_stock",
            "totalStock",
            "inventory",
            "metal_type",
            "metalType",
            "metal_karat",
            "metalKarat",
            "diamond_cut",
            "diamondCut",
            "styles",
            "stylesDetail",
            "diamond_type",
            "diamondTypeDetail",
            "brand",
            "brandDetail",
            "collections",
            "collectionsDetail",
            "diamond_spec",
            "earring_type",
            "earringType",
            "necklace_style",
            "necklaceStyle",
            "bracelet_type",
            "braceletType",
            "band_fit",
            "bandFit",
            "finish",
            "customisation_available",
            "customisationAvailable",
            "engraving_available",
            "engravingAvailable",
            "gender",
            "occasion",
            "is_active",
            "isActive",
            "is_featured",
            "isFeatured",
            "images",
            "sizes",
            "created_at",
            "updated_at",
        ]

    def get_pricing(self, obj):
        return {
            "basePrice": float(obj.base_price) if obj.base_price is not None else 0,
            "discountPrice": float(obj.discount_price) if obj.discount_price is not None else None,
            "taxPercentage": float(obj.tax_percentage) if obj.tax_percentage is not None else 0,
        }

    def get_inventory(self, obj):
        return {
            "totalStock": obj.total_stock,
            "lowStockThreshold": obj.low_stock_threshold,
        }

    def _sync_diamond_spec(self, product, diamond_spec_data):
        if diamond_spec_data is None:
            return
        DiamondSpecification.objects.update_or_create(product=product, defaults=diamond_spec_data)

    def create(self, validated_data):
        images_data = self.context.get("request").data.get("images", []) if self.context.get("request") else []
        sizes_data = self.context.get("request").data.get("sizes", []) if self.context.get("request") else []
        styles_data = validated_data.pop("styles", [])
        collections_data = validated_data.pop("collections", [])
        diamond_spec_data = validated_data.pop("diamond_spec", None)

        product = Product.objects.create(**validated_data)
        if styles_data:
            product.styles.set(styles_data)
        if collections_data:
            product.collections.set(collections_data)
        self._sync_diamond_spec(product, diamond_spec_data)

        if isinstance(images_data, list):
            for img in images_data:
                if isinstance(img, dict) and img.get("url"):
                    ProductImage.objects.create(
                        product=product,
                        url=img.get("url"),
                        public_id=img.get("publicId", img.get("public_id", "")),
                        is_primary=img.get("isPrimary", img.get("is_primary", False)),
                    )

        if isinstance(sizes_data, list):
            for sz in sizes_data:
                if isinstance(sz, dict) and sz.get("size"):
                    ProductSize.objects.create(
                        product=product,
                        size=str(sz.get("size")),
                        stock=int(sz.get("stock", 0)),
                    )

        return product

    def update(self, instance, validated_data):
        images_data = self.context.get("request").data.get("images") if self.context.get("request") else None
        sizes_data = self.context.get("request").data.get("sizes") if self.context.get("request") else None
        styles_data = validated_data.pop("styles", None)
        collections_data = validated_data.pop("collections", None)
        diamond_spec_data = validated_data.pop("diamond_spec", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if styles_data is not None:
            instance.styles.set(styles_data)
        if collections_data is not None:
            instance.collections.set(collections_data)
        self._sync_diamond_spec(instance, diamond_spec_data)

        if images_data is not None and isinstance(images_data, list):
            instance.images.all().delete()
            for img in images_data:
                if isinstance(img, dict) and img.get("url"):
                    ProductImage.objects.create(
                        product=instance,
                        url=img.get("url"),
                        public_id=img.get("publicId", img.get("public_id", "")),
                        is_primary=img.get("isPrimary", img.get("is_primary", False)),
                    )

        if sizes_data is not None and isinstance(sizes_data, list):
            instance.sizes.all().delete()
            for sz in sizes_data:
                if isinstance(sz, dict) and sz.get("size"):
                    ProductSize.objects.create(
                        product=instance,
                        size=str(sz.get("size")),
                        stock=int(sz.get("stock", 0)),
                    )

        return instance
