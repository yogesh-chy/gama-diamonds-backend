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
        ("necklaces", "Necklaces"),
        ("bracelets", "Bracelets"),
        ("earrings", "Earrings"),
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

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="rings")
    category_ref = models.ForeignKey(Category, related_name="products", on_delete=models.SET_NULL, null=True, blank=True)
    subcategory_ref = models.ForeignKey(Subcategory, related_name="products", on_delete=models.SET_NULL, null=True, blank=True)

    # Cross-cutting facets — how heeradiamonds.com actually lets you browse:
    # shop by style, shop by diamond type, shop by brand, curated collections.
    styles = models.ManyToManyField(Style, related_name="products", blank=True)
    diamond_type = models.ForeignKey(DiamondType, related_name="products", on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(Brand, related_name="products", on_delete=models.SET_NULL, null=True, blank=True)
    collections = models.ManyToManyField(Collection, related_name="products", blank=True)

    band_fit = models.CharField(max_length=20, choices=BAND_FIT_CHOICES, blank=True, null=True)
    finish = models.CharField(max_length=30, blank=True, default="")
    customisation_available = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")
    engraving_available = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="no")

    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    total_stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    metal_type = models.CharField(max_length=30, choices=METAL_TYPE_CHOICES, blank=True, null=True)
    metal_karat = models.CharField(max_length=20, choices=METAL_KARAT_CHOICES, blank=True, null=True)
    diamond_cut = models.CharField(max_length=30, choices=DIAMOND_CUT_CHOICES, blank=True, null=True)
    earring_type = models.CharField(max_length=30, choices=EARRING_TYPE_CHOICES, blank=True, null=True)
    necklace_style = models.CharField(max_length=30, choices=NECKLACE_STYLE_CHOICES, blank=True, null=True)
    bracelet_type = models.CharField(max_length=30, choices=BRACELET_TYPE_CHOICES, blank=True, null=True)

    gender = models.CharField(max_length=20, choices=[("women", "Women"), ("men", "Men"), ("unisex", "Unisex")], default="women")
    occasion = models.CharField(max_length=100, blank=True, default="")

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
    def price(self):
        if self.discount_price is not None and self.discount_price < self.base_price:
            return float(self.discount_price)
        return float(self.base_price)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
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
    """
    The 4Cs — the actual substance behind every product description on
    the reference site. One-to-one because carat/cut/colour/clarity are
    fixed per listing (see the pricing-model note: a different stone is a
    different product, matching how the real site is organized — not a
    live-recalculating variant on one listing).
    """
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

    product = models.OneToOneField(Product, related_name="diamond_spec", on_delete=models.CASCADE)

    carat_weight = models.DecimalField(max_digits=6, decimal_places=2)
    side_carat_weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cut_grade = models.CharField(max_length=20, choices=CUT_GRADE_CHOICES, blank=True, null=True)
    colour_grade = models.CharField(max_length=2, choices=COLOUR_GRADE_CHOICES, blank=True, null=True)
    clarity_grade = models.CharField(max_length=10, choices=CLARITY_GRADE_CHOICES, blank=True, null=True)

    certification_lab = models.CharField(max_length=10, choices=CERT_LAB_CHOICES, default="none")
    certificate_number = models.CharField(max_length=100, blank=True, default="")

    def __str__(self):
        return f"{self.carat_weight}ct {self.cut_grade or ''} — {self.product.name}"

