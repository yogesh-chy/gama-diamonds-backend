from django.db import transaction
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
    ProductVariant,
    Style,
    Subcategory,
)


class ProductImageSerializer(serializers.ModelSerializer):
    publicId = serializers.CharField(source="public_id", required=False, allow_blank=True)
    isPrimary = serializers.BooleanField(source="is_primary", required=False, default=False)
    variantId = serializers.IntegerField(source="variant_id", required=False, allow_null=True)

    class Meta:
        model = ProductImage
        fields = ["id", "url", "publicId", "isPrimary", "variantId"]


class ProductVariantSerializer(serializers.ModelSerializer):
    metalType = serializers.CharField(source="metal_type", required=False, allow_blank=True)
    metalKarat = serializers.CharField(source="metal_karat", required=False, allow_blank=True)
    metalWeightGrams = serializers.DecimalField(source="metal_weight_grams", max_digits=8, decimal_places=2, required=False, allow_null=True)
    compareAtPrice = serializers.DecimalField(source="compare_at_price", max_digits=12, decimal_places=2, required=False, allow_null=True)
    costPrice = serializers.DecimalField(source="cost_price", max_digits=12, decimal_places=2, required=False, allow_null=True)
    bangleSize = serializers.CharField(source="bangle_size", required=False, allow_blank=True)
    trackInventory = serializers.BooleanField(source="track_inventory", required=False)
    allowBackorder = serializers.BooleanField(source="allow_backorder", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)
    isDefault = serializers.BooleanField(source="is_default", required=False)
    images = ProductImageSerializer(many=True, required=False)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "metal_type",
            "metalType",
            "metal_karat",
            "metalKarat",
            "metal_weight_grams",
            "metalWeightGrams",
            "size",
            "length",
            "bangle_size",
            "bangleSize",
            "price",
            "compare_at_price",
            "compareAtPrice",
            "cost_price",
            "costPrice",
            "stock",
            "low_stock_threshold",
            "track_inventory",
            "trackInventory",
            "allow_backorder",
            "allowBackorder",
            "availability",
            "is_active",
            "isActive",
            "is_default",
            "isDefault",
            "images",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "sku": {"validators": []},
        }


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", "size", "stock"]


class SubcategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Subcategory
        fields = ["id", "category", "category_name", "name", "slug", "created_at"]
        extra_kwargs = {"slug": {"required": False, "allow_blank": True}}


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "subcategories", "created_at"]
        extra_kwargs = {"slug": {"required": False, "allow_blank": True}}


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
    diamondOrigin = serializers.CharField(source="diamond_origin", required=False)
    diamondShape = serializers.CharField(source="diamond_shape", required=False, allow_blank=True)
    caratWeight = serializers.DecimalField(source="carat_weight", max_digits=6, decimal_places=2, required=False)
    centerCaratWeight = serializers.DecimalField(source="center_carat_weight", max_digits=6, decimal_places=2, required=False, allow_null=True)
    sideCaratWeight = serializers.DecimalField(source="side_carat_weight", max_digits=6, decimal_places=2, required=False, allow_null=True)
    totalCaratWeight = serializers.DecimalField(source="total_carat_weight", max_digits=6, decimal_places=2, required=False, allow_null=True)
    numberOfDiamonds = serializers.IntegerField(source="number_of_diamonds", required=False, allow_null=True)
    cutGrade = serializers.CharField(source="cut_grade", required=False, allow_null=True, allow_blank=True)
    colourGrade = serializers.CharField(source="colour_grade", required=False, allow_null=True, allow_blank=True)
    clarityGrade = serializers.CharField(source="clarity_grade", required=False, allow_null=True, allow_blank=True)
    certificationLab = serializers.CharField(source="certification_lab", required=False)
    certificateNumber = serializers.CharField(source="certificate_number", required=False, allow_blank=True)
    certificateUrl = serializers.CharField(source="certificate_url", required=False, allow_blank=True)

    class Meta:
        model = DiamondSpecification
        fields = [
            "diamond_origin", "diamondOrigin",
            "diamond_shape", "diamondShape",
            "carat_weight", "caratWeight",
            "center_carat_weight", "centerCaratWeight",
            "side_carat_weight", "sideCaratWeight",
            "total_carat_weight", "totalCaratWeight",
            "number_of_diamonds", "numberOfDiamonds",
            "cut_grade", "cutGrade",
            "colour_grade", "colourGrade",
            "clarity_grade", "clarityGrade",
            "polish",
            "symmetry",
            "fluorescence",
            "certification_lab", "certificationLab",
            "certificate_number", "certificateNumber",
            "certificate_url", "certificateUrl",
        ]


class ProductListSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    secondaryImage = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    inventory = serializers.SerializerMethodField()
    totalStock = serializers.IntegerField(source="total_stock", read_only=True)
    basePrice = serializers.DecimalField(source="base_price", max_digits=12, decimal_places=2, read_only=True)
    discountPrice = serializers.DecimalField(source="discount_price", max_digits=12, decimal_places=2, read_only=True, allow_null=True)
    available = serializers.BooleanField(source="is_available", read_only=True)
    diamondTypeDetail = DiamondTypeSerializer(source="diamond_type", read_only=True)
    brandDetail = BrandSerializer(source="brand", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "category",
            "base_price",
            "basePrice",
            "discount_price",
            "discountPrice",
            "total_stock",
            "totalStock",
            "inventory",
            "images",
            "variants",
            "thumbnail",
            "secondaryImage",
            "price",
            "pricing",
            "available",
            "is_featured",
            "is_active",
            "diamondTypeDetail",
            "brandDetail",
            "created_at",
        ]

    def get_thumbnail(self, obj):
        first_img = obj.images.filter(is_primary=True).first() or obj.images.first()
        if first_img and first_img.url:
            return first_img.url
        for v in obj.variants.all():
            v_img = v.images.filter(is_primary=True).first() or v.images.first()
            if v_img and v_img.url:
                return v_img.url
        return None

    def get_secondaryImage(self, obj):
        imgs = list(obj.images.all())
        if len(imgs) > 1 and imgs[1].url:
            return imgs[1].url
        for v in obj.variants.all():
            v_imgs = list(v.images.all())
            if len(v_imgs) > 1 and v_imgs[1].url:
                return v_imgs[1].url
        return None

    def get_price(self, obj):
        return obj.price_range

    def get_pricing(self, obj):
        range_data = obj.price_range
        return {
            "basePrice": float(obj.base_price) if obj.base_price is not None else range_data["min"],
            "discountPrice": float(obj.discount_price) if obj.discount_price is not None else None,
            "taxPercentage": float(obj.tax_percentage) if obj.tax_percentage is not None else 0,
        }

    def get_inventory(self, obj):
        return {
            "totalStock": obj.total_stock if not obj.variants.exists() else sum(v.stock for v in obj.variants.all()),
            "lowStockThreshold": obj.low_stock_threshold,
        }


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False)
    variants = ProductVariantSerializer(many=True, required=False)
    sizes = ProductSizeSerializer(many=True, required=False)
    diamond_spec = DiamondSpecificationSerializer(required=False, allow_null=True)

    styles = serializers.PrimaryKeyRelatedField(many=True, queryset=Style.objects.all(), required=False)
    stylesDetail = StyleSerializer(source="styles", many=True, read_only=True)
    collections = serializers.PrimaryKeyRelatedField(many=True, queryset=Collection.objects.all(), required=False)
    collectionsDetail = CollectionSerializer(source="collections", many=True, read_only=True)
    diamond_type = serializers.PrimaryKeyRelatedField(queryset=DiamondType.objects.all(), required=False, allow_null=True)
    diamondTypeDetail = DiamondTypeSerializer(source="diamond_type", read_only=True)
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), required=False, allow_null=True)
    brandDetail = BrandSerializer(source="brand", read_only=True)
    related_products = serializers.PrimaryKeyRelatedField(many=True, queryset=Product.objects.all(), required=False)

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
    videoUrl = serializers.CharField(source="video_url", required=False, allow_blank=True, allow_null=True)

    seoTitle = serializers.CharField(source="seo_title", required=False, allow_blank=True)
    seoDescription = serializers.CharField(source="seo_description", required=False, allow_blank=True)
    seoKeywords = serializers.CharField(source="seo_keywords", required=False, allow_blank=True)

    price = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
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
            "product_code",
            "internal_reference",
            "category",
            "base_price",
            "discount_price",
            "basePrice",
            "discountPrice",
            "price",
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
            # Category-specific fields
            "ring_type",
            "ring_style",
            "ring_shape",
            "band_style",
            "band_fit",
            "bandFit",
            "band_width",
            "ring_profile",
            "ring_finish",
            "ring_thickness",
            "resizable",
            "earring_type",
            "earringType",
            "earring_style",
            "closure_type",
            "drop_length",
            "earring_width",
            "earring_height",
            "necklace_type",
            "necklace_style",
            "necklaceStyle",
            "chain_type",
            "chain_length",
            "pendant_included",
            "pendant_type",
            "pendant_shape",
            "pendant_height",
            "pendant_width",
            "pendant_depth",
            "chain_included",
            "clasp_type",
            "bracelet_type",
            "braceletType",
            "bracelet_style",
            "bracelet_length",
            "bracelet_width",
            "bracelet_thickness",
            "bangle_type",
            "inner_diameter",
            "bangle_width",
            "bangle_thickness",
            "opening_type",
            "bangle_size",
            "adjustable",
            # Gemstones
            "gemstone_included",
            "gemstone_type",
            "gemstone_shape",
            "gemstone_colour",
            "gemstone_carat_weight",
            "gemstone_count",
            "gemstone_origin",
            # Universal dimensions
            "height",
            "width",
            "length",
            "depth",
            "thickness",
            "weight",
            # Customisation & Shipping
            "finish",
            "customisation_available",
            "customisationAvailable",
            "engraving_available",
            "engravingAvailable",
            "engraving_character_limit",
            "engraving_instructions",
            "personalisation_available",
            "delivery_type",
            "estimated_delivery_time",
            "next_day_delivery_available",
            "made_to_order",
            "production_time",
            "shipping_weight",
            "gender",
            "occasion",
            "video_url",
            "videoUrl",
            # SEO
            "seo_title",
            "seoTitle",
            "seo_description",
            "seoDescription",
            "seo_keywords",
            "seoKeywords",
            "canonical_url",
            "og_title",
            "og_description",
            "og_image",
            "related_products",
            "is_active",
            "isActive",
            "is_featured",
            "isFeatured",
            "images",
            "variants",
            "options",
            "sizes",
            "created_at",
            "updated_at",
        ]

    def get_price(self, obj):
        return obj.price_range

    def get_options(self, obj):
        variants = obj.variants.filter(is_active=True)
        metals = list(dict.fromkeys([v.metal_type for v in variants if v.metal_type]))
        karats = list(dict.fromkeys([v.metal_karat for v in variants if v.metal_karat]))
        sizes = list(dict.fromkeys([v.size for v in variants if v.size]))
        lengths = list(dict.fromkeys([v.length for v in variants if v.length]))
        bangle_sizes = list(dict.fromkeys([v.bangle_size for v in variants if v.bangle_size]))
        return {
            "metal": metals,
            "karat": karats,
            "size": sizes,
            "length": lengths,
            "bangle_size": bangle_sizes,
        }

    def get_pricing(self, obj):
        range_data = obj.price_range
        return {
            "basePrice": float(obj.base_price) if obj.base_price is not None else range_data["min"],
            "discountPrice": float(obj.discount_price) if obj.discount_price is not None else None,
            "taxPercentage": float(obj.tax_percentage) if obj.tax_percentage is not None else 0,
        }

    def get_inventory(self, obj):
        return {
            "totalStock": obj.total_stock if not obj.variants.exists() else sum(v.stock for v in obj.variants.all()),
            "lowStockThreshold": obj.low_stock_threshold,
        }

    def _sync_diamond_spec(self, product, diamond_spec_data):
        if diamond_spec_data is None:
            return
        DiamondSpecification.objects.update_or_create(product=product, defaults=diamond_spec_data)

    def _sync_variants(self, product, variants_data):
        if variants_data is None:
            return
        
        seen_ids = []
        for idx, var_data in enumerate(variants_data):
            var_id = var_data.get("id")
            images_data = var_data.pop("images", [])
            sku_val = var_data.get("sku")
            if not sku_val:
                sku_val = f"{product.sku}-V{idx+1}"

            defaults = {
                "sku": sku_val,
                "metal_type": var_data.get("metal_type", var_data.get("metalType", "")),
                "metal_karat": var_data.get("metal_karat", var_data.get("metalKarat", "")),
                "size": str(var_data.get("size", "")),
                "length": str(var_data.get("length", "")),
                "bangle_size": str(var_data.get("bangle_size", var_data.get("bangleSize", ""))),
                "price": var_data.get("price", product.base_price or 0),
                "compare_at_price": var_data.get("compare_at_price", var_data.get("compareAtPrice", None)),
                "cost_price": var_data.get("cost_price", var_data.get("costPrice", None)),
                "stock": int(var_data.get("stock", 0)),
                "track_inventory": var_data.get("track_inventory", var_data.get("trackInventory", True)),
                "allow_backorder": var_data.get("allow_backorder", var_data.get("allowBackorder", False)),
                "availability": var_data.get("availability", "in_stock"),
                "is_active": var_data.get("is_active", var_data.get("isActive", True)),
                "is_default": var_data.get("is_default", var_data.get("isDefault", idx == 0)),
            }

            if var_id:
                variant, _ = ProductVariant.objects.update_or_create(id=var_id, product=product, defaults=defaults)
            else:
                variant, _ = ProductVariant.objects.update_or_create(sku=sku_val, product=product, defaults=defaults)
            
            seen_ids.append(variant.id)

            if isinstance(images_data, list) and len(images_data) > 0:
                ProductImage.objects.filter(variant=variant).delete()
                for img in images_data:
                    if isinstance(img, dict) and img.get("url"):
                        ProductImage.objects.create(
                            product=product,
                            variant=variant,
                            url=img.get("url"),
                            public_id=img.get("publicId", img.get("public_id", "")),
                            is_primary=img.get("isPrimary", img.get("is_primary", False)),
                        )
                        if not ProductImage.objects.filter(product=product, variant__isnull=True).exists():
                            ProductImage.objects.create(
                                product=product,
                                url=img.get("url"),
                                public_id=img.get("publicId", img.get("public_id", "")),
                                is_primary=True,
                            )

        if seen_ids:
            product.variants.exclude(id__in=seen_ids).delete()

        if product.variants.exists():
            calc_stock = sum(v.stock for v in product.variants.filter(is_active=True))
            if product.total_stock != calc_stock:
                product.total_stock = calc_stock
                product.save(update_fields=["total_stock"])

    @transaction.atomic
    def create(self, validated_data):
        images_data = validated_data.pop("images", None)
        if images_data is None and self.context.get("request"):
            images_data = self.context.get("request").data.get("images", [])

        variants_data = validated_data.pop("variants", None)
        if variants_data is None and self.context.get("request"):
            variants_data = self.context.get("request").data.get("variants", [])

        sizes_data = validated_data.pop("sizes", None)
        if sizes_data is None and self.context.get("request"):
            sizes_data = self.context.get("request").data.get("sizes", [])

        styles_data = validated_data.pop("styles", [])
        collections_data = validated_data.pop("collections", [])
        related_products_data = validated_data.pop("related_products", [])
        diamond_spec_data = validated_data.pop("diamond_spec", None)

        if "base_price" not in validated_data:
            validated_data["base_price"] = 0

        product = Product.objects.create(**validated_data)
        if styles_data:
            product.styles.set(styles_data)
        if collections_data:
            product.collections.set(collections_data)
        if related_products_data:
            product.related_products.set(related_products_data)

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

        if isinstance(variants_data, list) and len(variants_data) > 0:
            self._sync_variants(product, variants_data)
        else:
            ProductVariant.objects.create(
                product=product,
                sku=product.sku,
                metal_type=product.metal_type or "",
                metal_karat=product.metal_karat or "",
                size="",
                price=product.price,
                compare_at_price=product.base_price if product.discount_price else None,
                stock=product.total_stock,
                is_default=True,
                is_active=product.is_active,
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

    @transaction.atomic
    def update(self, instance, validated_data):
        images_data = validated_data.pop("images", None)
        if images_data is None and self.context.get("request"):
            images_data = self.context.get("request").data.get("images")

        variants_data = validated_data.pop("variants", None)
        if variants_data is None and self.context.get("request"):
            variants_data = self.context.get("request").data.get("variants")

        sizes_data = validated_data.pop("sizes", None)
        if sizes_data is None and self.context.get("request"):
            sizes_data = self.context.get("request").data.get("sizes")

        styles_data = validated_data.pop("styles", None)
        collections_data = validated_data.pop("collections", None)
        related_products_data = validated_data.pop("related_products", None)
        diamond_spec_data = validated_data.pop("diamond_spec", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if styles_data is not None:
            instance.styles.set(styles_data)
        if collections_data is not None:
            instance.collections.set(collections_data)
        if related_products_data is not None:
            instance.related_products.set(related_products_data)

        self._sync_diamond_spec(instance, diamond_spec_data)

        if images_data is not None and isinstance(images_data, list):
            if len(images_data) > 0:
                instance.images.filter(variant__isnull=True).delete()
                for img in images_data:
                    if isinstance(img, dict) and img.get("url"):
                        ProductImage.objects.create(
                            product=instance,
                            url=img.get("url"),
                            public_id=img.get("publicId", img.get("public_id", "")),
                            is_primary=img.get("isPrimary", img.get("is_primary", False)),
                        )

        if variants_data is not None and isinstance(variants_data, list):
            self._sync_variants(instance, variants_data)

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


