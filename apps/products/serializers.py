import uuid
from django.db import transaction
from django.utils.text import slugify
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
    diamond_spec = DiamondSpecificationSerializer(read_only=True)
    diamondSpec = DiamondSpecificationSerializer(source="diamond_spec", read_only=True)
    thumbnail = serializers.SerializerMethodField()
    secondaryImage = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    inventory = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    totalStock = serializers.IntegerField(source="total_stock", read_only=True)
    basePrice = serializers.DecimalField(source="base_price", max_digits=12, decimal_places=2, read_only=True)
    discountPrice = serializers.DecimalField(source="discount_price", max_digits=12, decimal_places=2, read_only=True, allow_null=True)
    metalType = serializers.CharField(source="metal_type", read_only=True)
    metalKarat = serializers.CharField(source="metal_karat", read_only=True)
    diamondCut = serializers.CharField(source="diamond_cut", read_only=True)
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
            "category_ref",
            "subcategory_ref",
            "subcategory",
            "gender",
            "ring_type",
            "ring_style",
            "earring_type",
            "necklace_style",
            "bracelet_type",
            "base_price",
            "basePrice",
            "discount_price",
            "discountPrice",
            "total_stock",
            "totalStock",
            "inventory",
            "metal_type",
            "metalType",
            "metal_karat",
            "metalKarat",
            "diamond_cut",
            "diamondCut",
            "diamond_spec",
            "diamondSpec",
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

    def get_subcategory(self, obj):
        if obj.subcategory_ref:
            return obj.subcategory_ref.name
        return obj.ring_type or obj.ring_style or obj.earring_type or obj.necklace_style or obj.bracelet_type or ""

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
    subcategory = serializers.SerializerMethodField()

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
            "category_ref",
            "subcategory_ref",
            "subcategory",
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
        
        valid_fields = {
            "diamond_origin", "diamond_shape", "carat_weight",
            "center_carat_weight", "side_carat_weight", "total_carat_weight",
            "number_of_diamonds", "cut_grade", "colour_grade", "clarity_grade",
            "polish", "symmetry", "fluorescence", "certification_lab",
            "certificate_number", "certificate_url"
        }
        cleaned_data = {}
        for k, v in diamond_spec_data.items():
            snake_k = k
            if k == "diamondOrigin": snake_k = "diamond_origin"
            elif k == "diamondShape": snake_k = "diamond_shape"
            elif k == "caratWeight": snake_k = "carat_weight"
            elif k == "centerCaratWeight": snake_k = "center_carat_weight"
            elif k == "sideCaratWeight": snake_k = "side_carat_weight"
            elif k == "totalCaratWeight": snake_k = "total_carat_weight"
            elif k == "numberOfDiamonds": snake_k = "number_of_diamonds"
            elif k == "cutGrade": snake_k = "cut_grade"
            elif k == "colourGrade": snake_k = "colour_grade"
            elif k == "clarityGrade": snake_k = "clarity_grade"
            elif k == "certificationLab": snake_k = "certification_lab"
            elif k == "certificateNumber": snake_k = "certificate_number"
            elif k == "certificateUrl": snake_k = "certificate_url"

            if snake_k in valid_fields and v is not None:
                cleaned_data[snake_k] = v

        if not cleaned_data.get("carat_weight") and cleaned_data.get("total_carat_weight"):
            cleaned_data["carat_weight"] = cleaned_data["total_carat_weight"]
        elif not cleaned_data.get("carat_weight"):
            cleaned_data["carat_weight"] = 1.0

        try:
            DiamondSpecification.objects.update_or_create(product=product, defaults=cleaned_data)
        except Exception:
            spec = DiamondSpecification.objects.filter(product=product).first()
            if spec:
                for attr, val in cleaned_data.items():
                    setattr(spec, attr, val)
                spec.save()

        # Always align product.diamond_type from diamond_origin
        origin = cleaned_data.get("diamond_origin")
        if origin:
            target_name = "Natural" if origin == "natural" else "Lab-Grown"
            dt = DiamondType.objects.filter(name__iexact=target_name).first()
            if not dt:
                dt = DiamondType.objects.filter(slug__iexact=slugify(target_name)).first()
            if not dt:
                try:
                    dt = DiamondType.objects.create(name=target_name, slug=slugify(target_name))
                except Exception:
                    dt = DiamondType.objects.filter(name__iexact=target_name).first()
            if dt and product.diamond_type != dt:
                product.diamond_type = dt
                product.save(update_fields=["diamond_type"])

    def _sync_variants(self, product, variants_data):
        if variants_data is None:
            return
        
        seen_ids = []
        for idx, var_data in enumerate(variants_data):
            var_data = dict(var_data)
            var_id = var_data.get("id")
            images_data = var_data.pop("images", [])
            sku_val = var_data.get("sku") or f"{product.sku}-V{idx+1}"

            def _pick(snake, camel, fallback=None):
                val = var_data.get(snake)
                if val is not None and val != "":
                    return val
                val = var_data.get(camel)
                if val is not None and val != "":
                    return val
                return fallback

            defaults = {
                "sku": sku_val,
                "metal_type": _pick("metal_type", "metalType", product.metal_type or "yellow-gold"),
                "metal_karat": _pick("metal_karat", "metalKarat", product.metal_karat or "18K"),
                "metal_weight_grams": _pick("metal_weight_grams", "metalWeightGrams", None),
                "size": str(var_data.get("size", "")),
                "length": str(var_data.get("length", "")),
                "bangle_size": str(_pick("bangle_size", "bangleSize", "")),
                "price": var_data.get("price", product.base_price or 0),
                "compare_at_price": _pick("compare_at_price", "compareAtPrice", None),
                "cost_price": _pick("cost_price", "costPrice", None),
                "stock": int(var_data.get("stock", 0)),
                "track_inventory": _pick("track_inventory", "trackInventory", True),
                "allow_backorder": _pick("allow_backorder", "allowBackorder", False),
                "availability": var_data.get("availability", "in_stock"),
                "is_active": _pick("is_active", "isActive", True),
                "is_default": _pick("is_default", "isDefault", idx == 0),
            }

            variant = None
            if var_id:
                variant = ProductVariant.objects.filter(id=var_id, product=product).first()
            if not variant:
                variant = ProductVariant.objects.filter(sku=sku_val, product=product).first()
            if not variant:
                variant = ProductVariant.objects.filter(
                    product=product,
                    metal_type=defaults["metal_type"],
                    metal_karat=defaults["metal_karat"],
                    size=defaults["size"],
                    length=defaults["length"],
                    bangle_size=defaults["bangle_size"],
                ).first()
            if not variant and len(variants_data) == 1:
                variant = product.variants.first()

            if variant:
                # Delete any other variant that has the same combination to prevent UniqueConstraint violation
                ProductVariant.objects.filter(
                    product=product,
                    metal_type=defaults["metal_type"],
                    metal_karat=defaults["metal_karat"],
                    size=defaults["size"],
                    length=defaults["length"],
                    bangle_size=defaults["bangle_size"],
                ).exclude(id=variant.id).delete()

                # Ensure SKU is not taken by another variant outside this product
                sku_conflict = ProductVariant.objects.filter(sku=defaults["sku"]).exclude(id=variant.id).exists()
                if sku_conflict:
                    defaults["sku"] = f"{product.sku}-{uuid.uuid4().hex[:4].upper()}"

                for attr, val in defaults.items():
                    setattr(variant, attr, val)
                variant.save()
            else:
                conflicting = ProductVariant.objects.filter(
                    product=product,
                    metal_type=defaults["metal_type"],
                    metal_karat=defaults["metal_karat"],
                    size=defaults["size"],
                    length=defaults["length"],
                    bangle_size=defaults["bangle_size"],
                ).first()
                if conflicting:
                    variant = conflicting
                    for attr, val in defaults.items():
                        setattr(variant, attr, val)
                    variant.save()
                else:
                    if ProductVariant.objects.filter(sku=defaults["sku"]).exists():
                        defaults["sku"] = f"{product.sku}-{uuid.uuid4().hex[:4].upper()}"
                    variant = ProductVariant.objects.create(product=product, **defaults)
            
            seen_ids.append(variant.id)

            if defaults.get("is_default") or idx == 0:
                prod_updates = []
                if defaults.get("metal_type") and product.metal_type != defaults.get("metal_type"):
                    product.metal_type = defaults.get("metal_type")
                    prod_updates.append("metal_type")
                if defaults.get("metal_karat") and product.metal_karat != defaults.get("metal_karat"):
                    product.metal_karat = defaults.get("metal_karat")
                    prod_updates.append("metal_karat")
                if defaults.get("price") is not None and product.base_price != defaults.get("price"):
                    product.base_price = defaults.get("price")
                    prod_updates.append("base_price")
                if prod_updates:
                    product.save(update_fields=prod_updates)

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

    def get_subcategory(self, obj):
        if obj.subcategory_ref:
            return obj.subcategory_ref.name
        return obj.ring_type or obj.ring_style or obj.earring_type or obj.necklace_style or obj.bracelet_type or ""

    def _sync_taxonomy(self, product, raw_data=None):
        try:
            raw = raw_data or {}
            cat_slug = product.category or raw.get("category")
            cat_obj = None
            if cat_slug:
                cat_slug_clean = slugify(str(cat_slug))
                cat_clean_name = str(cat_slug).replace("-", " ").title()
                cat_obj = (
                    Category.objects.filter(slug__iexact=cat_slug_clean).first()
                    or Category.objects.filter(slug__iexact=cat_slug).first()
                    or Category.objects.filter(name__iexact=cat_clean_name).first()
                    or Category.objects.filter(name__iexact=cat_slug).first()
                )
                if not cat_obj and cat_slug_clean:
                    try:
                        cat_obj = Category.objects.create(name=cat_clean_name, slug=cat_slug_clean)
                    except Exception:
                        cat_obj = Category.objects.filter(slug__iexact=cat_slug_clean).first()

                if cat_obj and product.category_ref != cat_obj:
                    product.category_ref = cat_obj
                    product.save(update_fields=["category_ref"])

            sub_name = (
                raw.get("subcategory")
                or raw.get("ring_type")
                or raw.get("ring_style")
                or raw.get("earring_type")
                or raw.get("necklace_style")
                or raw.get("bracelet_type")
                or product.ring_type
                or product.ring_style
                or product.earring_type
                or product.necklace_style
                or product.bracelet_type
            )
            if sub_name:
                sub_str = str(sub_name).strip()
                updated_fields = []
                cat_type = str(product.category or "").lower()

                if "earring" in cat_type:
                    if not product.earring_type:
                        product.earring_type = sub_str
                        updated_fields.append("earring_type")
                    if not product.earring_style:
                        product.earring_style = sub_str
                        updated_fields.append("earring_style")
                elif "necklace" in cat_type or "pendant" in cat_type:
                    if not product.necklace_style:
                        product.necklace_style = sub_str
                        updated_fields.append("necklace_style")
                elif "bracelet" in cat_type or "bangle" in cat_type:
                    if not product.bracelet_type:
                        product.bracelet_type = sub_str
                        updated_fields.append("bracelet_type")
                else:
                    if not product.ring_type:
                        product.ring_type = sub_str
                        updated_fields.append("ring_type")
                    if not product.ring_style:
                        product.ring_style = sub_str
                        updated_fields.append("ring_style")

                if product.category_ref:
                    sub_slug = slugify(sub_str)
                    if sub_slug:
                        sub_obj = (
                            Subcategory.objects.filter(category=product.category_ref, slug__iexact=sub_slug).first()
                            or Subcategory.objects.filter(category=product.category_ref, name__iexact=sub_str).first()
                        )
                        if not sub_obj:
                            try:
                                sub_obj = Subcategory.objects.create(category=product.category_ref, name=sub_str, slug=sub_slug)
                            except Exception:
                                sub_obj = Subcategory.objects.filter(category=product.category_ref, slug__iexact=sub_slug).first()

                        if sub_obj and product.subcategory_ref != sub_obj:
                            product.subcategory_ref = sub_obj
                            updated_fields.append("subcategory_ref")

                if updated_fields:
                    product.save(update_fields=updated_fields)

                st_slug = slugify(sub_str)
                if st_slug:
                    style_obj = Style.objects.filter(slug__iexact=st_slug).first() or Style.objects.filter(name__iexact=sub_str).first()
                    if not style_obj:
                        try:
                            style_obj = Style.objects.create(name=sub_str, slug=st_slug)
                        except Exception:
                            style_obj = Style.objects.filter(slug__iexact=st_slug).first()
                    if style_obj:
                        product.styles.add(style_obj)
        except Exception:
            pass

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

        raw_req_data = self.context.get("request").data if self.context.get("request") else {}
        self._sync_taxonomy(product, raw_req_data)
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
        if diamond_spec_data is None and self.context.get("request"):
            diamond_spec_data = self.context.get("request").data.get("diamond_spec") or self.context.get("request").data.get("diamondSpec")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if styles_data is not None:
            instance.styles.set(styles_data)
        if collections_data is not None:
            instance.collections.set(collections_data)
        if related_products_data is not None:
            instance.related_products.set(related_products_data)

        raw_req_data = self.context.get("request").data if self.context.get("request") else {}
        self._sync_taxonomy(instance, raw_req_data)
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


