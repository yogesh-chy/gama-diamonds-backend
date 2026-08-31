import uuid
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    category = models.ForeignKey(Category, related_name="subcategories", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Subcategories"
        unique_together = ["category", "slug"]
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} -> {self.name}"


class Style(models.Model):
    """
    Cross-cutting style tags (Solitaire, Halo, Diamond Shoulder, Trilogy
    Three Stone, Traditional Court, ...). Many-to-many on purpose: real
    products are tagged with more than one at once — e.g. a "Solitaire
    Diamond Shoulder" ring is both styles simultaneously, which a
    single-choice field can't represent.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DiamondType(models.Model):
    """Natural / Lab-Grown / Coloured — a first-class nav axis on the
    reference site ("Select Diamond Type"), not just a buried filter."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    """Third-party brands (e.g. Hot Diamonds). Most products won't have
    one — house-made pieces leave this null."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Collection(models.Model):
    """
    Curated/marketing groupings that cut across category, style, and
    everything else — New Arrivals, Next Day Delivery, and "The Classics"
    (Tennis Bracelets, Solitaire Studs, Heart Pendants, Cross Pendants,
    Hoop Earrings). A product's category doesn't change; it just also
    gets featured in one or more of these.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

import uuid
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    category = models.ForeignKey(Category, related_name="subcategories", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Subcategories"
        unique_together = ["category", "slug"]
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} -> {self.name}"


class Style(models.Model):
    """
    Cross-cutting style tags (Solitaire, Halo, Diamond Shoulder, Trilogy
    Three Stone, Traditional Court, ...). Many-to-many on purpose: real
    products are tagged with more than one at once — e.g. a "Solitaire
    Diamond Shoulder" ring is both styles simultaneously, which a
    single-choice field can't represent.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DiamondType(models.Model):
    """Natural / Lab-Grown / Coloured — a first-class nav axis on the
    reference site ("Select Diamond Type"), not just a buried filter."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    """Third-party brands (e.g. Hot Diamonds). Most products won't have
    one — house-made pieces leave this null."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Collection(models.Model):
    """
    Curated/marketing groupings that cut across category, style, and
    everything else — New Arrivals, Next Day Delivery, and "The Classics"
    (Tennis Bracelets, Solitaire Studs, Heart Pendants, Cross Pendants,
    Hoop Earrings). A product's category doesn't change; it just also
    gets featured in one or more of these.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("rings", "Rings"),
        ("engagement-rings", "Engagement Rings"),
        ("wedding-bands", "Wedding Bands"),
        ("eternity-bands", "Eternity Bands"),
        ("necklaces", "Necklaces"),
        ("pendants", "Pendants"),
        ("bracelets", "Bracelets"),
        ("bangles", "Bangles"),
        ("earrings", "Earrings"),
        ("other", "Other Jewellery"),
    ]

    METAL_TYPE_CHOICES = [
        ("yellow-gold", "Yellow Gold"),
        ("white-gold", "White Gold"),
        ("rose-gold", "Rose Gold"),
        ("platinum", "Platinum"),
        ("silver", "Silver"),
        ("two-tone", "Two-Tone"),
    ]

    METAL_KARAT_CHOICES = [
        ("9K", "9ct"),
        ("10K", "10ct"),
        ("14K", "14ct"),
        ("18K", "18ct"),
        ("22K", "22ct"),
        ("24K", "24ct"),
        ("950Pt", "950 Platinum"),
        ("925Ag", "925 Silver"),
    ]

    DIAMOND_CUT_CHOICES = [
        ("round", "Round Brilliant"),
        ("princess", "Princess"),
        ("oval", "Oval"),
        ("pear", "Pear"),
        ("cushion", "Cushion"),
        ("emerald-cut", "Emerald"),
        ("radiant", "Radiant Cut"),
        ("marquise", "Marquise"),
        ("asscher", "Asscher"),
        ("heart", "Heart"),
    ]

    EARRING_TYPE_CHOICES = [
        ("studs", "Studs"),
        ("hoops", "Hoops"),
        ("drops", "Drops"),
        ("huggies", "Huggies"),
        ("climbers", "Climbers"),
        ("chandelier", "Chandelier"),
    ]

    NECKLACE_STYLE_CHOICES = [
        ("pendant", "Pendant"),
        ("chain", "Chain"),
        ("choker", "Choker"),
        ("collar", "Collar"),
        ("station", "Station"),
        ("lariat", "Lariat"),
        ("tennis", "Tennis"),
    ]

    BRACELET_TYPE_CHOICES = [
        ("bangle", "Bangle"),
        ("tennis", "Tennis"),
        ("chain", "Chain"),
        ("cuff", "Cuff"),
        ("charm", "Charm"),
        ("link", "Link"),
    ]

    BAND_FIT_CHOICES = [
        ("comfort", "Comfort Fit"),
        ("standard", "Standard/Traditional Fit"),
    ]
    AVAILABILITY_CHOICES = [
        ("yes", "Yes"),
        ("on_request", "On Request"),
        ("no", "No"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True, default="")

    product_code = models.CharField(max_length=50, blank=True, default="")
    internal_reference = models.CharField(max_length=100, blank=True, default="")

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="rings")
    category_ref = models.ForeignKey(Category, related_name="products", on_delete=models.SET_NULL, null=True, blank=True)
    subcategory_ref = models.ForeignKey(Subcategory, related_name="products", on_delete=models.SET_NULL, null=True, blank=True)

    styles = models.ManyToManyField(Style, related_name="products", blank=True)
    diamond_type = models.ForeignKey(DiamondType, related_name="products", on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(Brand, related_name="products", on_delete=models.SET_NULL, null=True, blank=True)
    collections = models.ManyToManyField(Collection, related_name="products", blank=True)

    # Ring Fields
    ring_type = models.CharField(max_length=50, blank=True, default="")
    ring_style = models.CharField(max_length=50, blank=True, default="")
    ring_shape = models.CharField(max_length=50, blank=True, default="")
    band_style = models.CharField(max_length=50, blank=True, default="")
    band_fit = models.CharField(max_length=20, choices=BAND_FIT_CHOICES, blank=True, null=True)
    band_width = models.CharField(max_length=30, blank=True, default="")
    ring_profile = models.CharField(max_length=50, blank=True, default="")
    ring_finish = models.CharField(max_length=50, blank=True, default="")
    ring_thickness = models.CharField(max_length=30, blank=True, default="")
    resizable = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="yes")

    # Earring Fields
    earring_type = models.CharField(max_length=30, choices=EARRING_TYPE_CHOICES, blank=True, null=True)
    earring_style = models.CharField(max_length=50, blank=True, default="")
    closure_type = models.CharField(max_length=50, blank=True, default="")
    drop_length = models.CharField(max_length=30, blank=True, default="")
    earring_width = models.CharField(max_length=30, blank=True, default="")
    earring_height = models.CharField(max_length=30, blank=True, default="")

    # Necklace & Pendant Fields
    necklace_type = models.CharField(max_length=50, blank=True, default="")
    necklace_style = models.CharField(max_length=30, choices=NECKLACE_STYLE_CHOICES, blank=True, null=True)
    chain_type = models.CharField(max_length=50, blank=True, default="")
    chain_length = models.CharField(max_length=50, blank=True, default="")
    pendant_included = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")
    pendant_type = models.CharField(max_length=50, blank=True, default="")
    pendant_shape = models.CharField(max_length=50, blank=True, default="")
    pendant_height = models.CharField(max_length=30, blank=True, default="")
    pendant_width = models.CharField(max_length=30, blank=True, default="")
    pendant_depth = models.CharField(max_length=30, blank=True, default="")
    chain_included = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")
    clasp_type = models.CharField(max_length=50, blank=True, default="")

    # Bracelet & Bangle Fields
    bracelet_type = models.CharField(max_length=30, choices=BRACELET_TYPE_CHOICES, blank=True, null=True)
    bracelet_style = models.CharField(max_length=50, blank=True, default="")
    bracelet_length = models.CharField(max_length=50, blank=True, default="")
    bracelet_width = models.CharField(max_length=30, blank=True, default="")
    bracelet_thickness = models.CharField(max_length=30, blank=True, default="")
    bangle_type = models.CharField(max_length=50, blank=True, default="")
    inner_diameter = models.CharField(max_length=30, blank=True, default="")
    bangle_width = models.CharField(max_length=30, blank=True, default="")
    bangle_thickness = models.CharField(max_length=30, blank=True, default="")
    opening_type = models.CharField(max_length=50, blank=True, default="")
    bangle_size = models.CharField(max_length=30, blank=True, default="")
    adjustable = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")

    # Gemstone Fields
    gemstone_included = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")
    gemstone_type = models.CharField(max_length=50, blank=True, default="")
    gemstone_shape = models.CharField(max_length=50, blank=True, default="")
    gemstone_colour = models.CharField(max_length=50, blank=True, default="")
    gemstone_carat_weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    gemstone_count = models.PositiveIntegerField(null=True, blank=True)
    gemstone_origin = models.CharField(max_length=50, blank=True, default="")

    # Universal Dimensions
    height = models.CharField(max_length=30, blank=True, default="")
    width = models.CharField(max_length=30, blank=True, default="")
    length = models.CharField(max_length=30, blank=True, default="")
    depth = models.CharField(max_length=30, blank=True, default="")
    thickness = models.CharField(max_length=30, blank=True, default="")
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # General Attributes
    finish = models.CharField(max_length=30, blank=True, default="")
    customisation_available = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")
    engraving_available = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")
    engraving_character_limit = models.PositiveIntegerField(default=25)
    engraving_instructions = models.TextField(blank=True, default="")
    personalisation_available = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")

    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    total_stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    metal_type = models.CharField(max_length=30, choices=METAL_TYPE_CHOICES, blank=True, null=True)
    metal_karat = models.CharField(max_length=20, choices=METAL_KARAT_CHOICES, blank=True, null=True)
    diamond_cut = models.CharField(max_length=30, choices=DIAMOND_CUT_CHOICES, blank=True, null=True)

    gender = models.CharField(max_length=20, choices=[("women", "Women"), ("men", "Men"), ("unisex", "Unisex")], default="women")
    occasion = models.CharField(max_length=100, blank=True, default="")

    video_url = models.CharField(max_length=1000, blank=True, default="")

    # Shipping & Delivery
    delivery_type = models.CharField(max_length=50, blank=True, default="Standard Secure Shipping")
    estimated_delivery_time = models.CharField(max_length=100, blank=True, default="3-5 Business Days")
    next_day_delivery_available = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")
    made_to_order = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")
    production_time = models.CharField(max_length=100, blank=True, default="")
    shipping_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # SEO & Canonical
    seo_title = models.CharField(max_length=255, blank=True, default="")
    seo_description = models.TextField(blank=True, default="")
    seo_keywords = models.CharField(max_length=255, blank=True, default="")
    canonical_url = models.URLField(max_length=500, blank=True, default="")
    og_title = models.CharField(max_length=255, blank=True, default="")
    og_description = models.TextField(blank=True, default="")
    og_image = models.URLField(max_length=1000, blank=True, default="")

    related_products = models.ManyToManyField("self", symmetrical=False, blank=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "product"
            slug = base
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug

        if not self.sku:
            prefix = self.category[:3].upper() if self.category else "PRD"
            random_part = uuid.uuid4().hex[:6].upper()
            self.sku = f"GAMA-{prefix}-{random_part}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def active_variants(self):
        return self.variants.filter(is_active=True)

    @property
    def price_range(self):
        variants = list(self.active_variants)
        if variants:
            prices = [v.price for v in variants if v.price is not None]
            if prices:
                min_p = min(prices)
                max_p = max(prices)
                display_str = f"£{min_p:,.2f}" if min_p == max_p else f"From £{min_p:,.2f}"
                return {
                    "min": float(min_p),
                    "max": float(max_p),
                    "display": display_str,
                }
        base = float(self.base_price) if self.base_price is not None else 0.0
        disc = float(self.discount_price) if self.discount_price is not None and self.discount_price < self.base_price else base
        return {
            "min": disc,
            "max": base,
            "display": f"£{disc:,.2f}",
        }

    @property
    def price(self):
        range_data = self.price_range
        return range_data["min"]

    @property
    def is_available(self):
        variants = list(self.active_variants)
        if variants:
            return any(v.stock > 0 for v in variants)
        return self.total_stock > 0


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True)
    metal_type = models.CharField(max_length=30, choices=Product.METAL_TYPE_CHOICES, blank=True, default="")
    metal_karat = models.CharField(max_length=20, choices=Product.METAL_KARAT_CHOICES, blank=True, default="")
    size = models.CharField(max_length=50, blank=True, default="")
    length = models.CharField(max_length=50, blank=True, default="")
    bangle_size = models.CharField(max_length=50, blank=True, default="")
    metal_weight_grams = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    track_inventory = models.BooleanField(default=True)
    allow_backorder = models.BooleanField(default=False)
    availability = models.CharField(max_length=30, default="in_stock")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "metal_type", "metal_karat", "size", "length", "bangle_size"],
                name="unique_product_variant_combination"
            )
        ]

    def __str__(self):
        details = [d for d in [
            self.metal_type,
            self.metal_karat,
            f"Size {self.size}" if self.size else "",
            f"Length {self.length}" if self.length else "",
            f"Bangle Size {self.bangle_size}" if self.bangle_size else ""
        ] if d]
        detail_str = f" ({', '.join(details)})" if details else ""
        return f"{self.product.name} — {self.sku}{detail_str}"

    @property
    def display_price(self):
        return float(self.price)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, related_name="images", on_delete=models.CASCADE, null=True, blank=True)
    url = models.URLField(max_length=1000)
    public_id = models.CharField(max_length=255, blank=True, default="")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "id"]


class ProductSize(models.Model):
    product = models.ForeignKey(Product, related_name="sizes", on_delete=models.CASCADE)
    size = models.CharField(max_length=50)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["size"]


class DiamondSpecification(models.Model):
    CUT_GRADE_CHOICES = [
        ("excellent", "Excellent"),
        ("very_good", "Very Good"),
        ("good", "Good"),
        ("fair", "Fair"),
    ]
    COLOUR_GRADE_CHOICES = [(g, g) for g in "DEFGHIJKLMNOPQRSTUVWXYZ"]
    CLARITY_GRADE_CHOICES = [
        ("FL", "Flawless"), ("IF", "Internally Flawless"),
        ("VVS1", "VVS1"), ("VVS2", "VVS2"),
        ("VS1", "VS1"), ("VS2", "VS2"),
        ("SI1", "SI1"), ("SI2", "SI2"),
        ("I1", "I1"), ("I2", "I2"), ("I3", "I3"),
    ]
    CERT_LAB_CHOICES = [
        ("GIA", "GIA"), ("IGI", "IGI"), ("none", "Uncertified"),
    ]
    DIAMOND_ORIGIN_CHOICES = [
        ("lab_grown", "Lab Grown"),
        ("natural", "Natural"),
    ]

    product = models.OneToOneField(Product, related_name="diamond_spec", on_delete=models.CASCADE)

    diamond_origin = models.CharField(max_length=20, choices=DIAMOND_ORIGIN_CHOICES, default="lab_grown")
    diamond_shape = models.CharField(max_length=50, blank=True, default="")
    carat_weight = models.DecimalField(max_digits=6, decimal_places=2)
    center_carat_weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    side_carat_weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    total_carat_weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    number_of_diamonds = models.PositiveIntegerField(null=True, blank=True)

    cut_grade = models.CharField(max_length=20, choices=CUT_GRADE_CHOICES, blank=True, null=True)
    colour_grade = models.CharField(max_length=2, choices=COLOUR_GRADE_CHOICES, blank=True, null=True)
    clarity_grade = models.CharField(max_length=10, choices=CLARITY_GRADE_CHOICES, blank=True, null=True)
    polish = models.CharField(max_length=20, blank=True, default="")
    symmetry = models.CharField(max_length=20, blank=True, default="")
    fluorescence = models.CharField(max_length=20, blank=True, default="")

    certification_lab = models.CharField(max_length=10, choices=CERT_LAB_CHOICES, default="none")
    certificate_number = models.CharField(max_length=100, blank=True, default="")
    certificate_url = models.URLField(max_length=1000, blank=True, default="")

    def __str__(self):
        return f"{self.carat_weight}ct {self.cut_grade or ''} — {self.product.name}"
