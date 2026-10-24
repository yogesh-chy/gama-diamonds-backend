from django.core.management.base import BaseCommand
from products.models import Category, Subcategory, Product, ProductImage, ProductSize, Style


class Command(BaseCommand):
    help = "Seeds initial sample jewellery categories, subcategories, and products into the database"

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories and products...")

        # 1. Main 7 Categories and Subcategories
        category_data = [
            {
                "name": "Engagement Rings",
                "slug": "engagement-rings",
                "subcategories": [
                    ("Solitaire", "solitaire"),
                    ("Halo", "halo"),
                    ("Under Halo", "under-halo"),
                    ("Diamond Shoulder", "diamond-shoulder"),
                    ("Trilogy Three Stone", "three-stone"),
                    ("Matching Set", "matching-set"),
                ],
            },
            {
                "name": "Wedding Rings",
                "slug": "wedding-rings",
                "subcategories": [
                    ("Women's Plain", "womens-plain"),
                    ("Eternity Rings", "eternity-rings"),
                    ("Men's Plain", "mens-plain"),
                    ("Men's Diamond", "mens-diamond"),
                    ("Men's Pattern", "mens-pattern"),
                    ("Traditional Court", "traditional-court"),
                    ("Flat Court", "flat-court"),
                    ("Soft Court", "soft-court"),
                ],
            },
            {
                "name": "Eternity Rings",
                "slug": "eternity-rings",
                "subcategories": [
                    ("Full Eternity", "full-eternity"),
                    ("Half Eternity", "half-eternity"),
                    ("Seven Stone", "seven-stone"),
                    ("Micro-Pave", "micro-pave"),
                ],
            },
            {
                "name": "Earrings",
                "slug": "earrings",
                "subcategories": [
                    ("Solitaire Studs", "solitaire-studs"),
                    ("Hoop Earrings", "hoop-earrings"),
                    ("Drop Earrings", "drop-earrings"),
                    ("Halo Earrings", "halo-earrings"),
                    ("Chandelier Earrings", "chandelier-earrings"),
                ],
            },
            {
                "name": "Necklace",
                "slug": "necklaces",
                "subcategories": [
                    ("Pendants", "pendants"),
                    ("Heart Pendants", "heart-pendants"),
                    ("Cross Pendants", "cross-pendants"),
                    ("Tennis Necklaces", "tennis-necklaces"),
                    ("Chains", "chains"),
                ],
            },
            {
                "name": "Bracelets",
                "slug": "bracelets",
                "subcategories": [
                    ("Tennis Bracelets", "tennis-bracelets"),
                    ("Bangles", "bangles"),
                    ("Cuff Bracelets", "cuff-bracelets"),
                    ("Chain Bracelets", "chain-bracelets"),
                ],
            },
            {
                "name": "Jewellery",
                "slug": "jewellery",
                "subcategories": [
                    ("Statement Rings", "statement-rings"),
                    ("Gold Colour", "gold-colour"),
                    ("Silver Colour", "silver-colour"),
                    ("Rose Gold", "rose-gold"),
                    ("The Classics", "the-classics"),
                    ("Hot Diamonds", "hot-diamonds"),
                ],
            },
        ]

        cat_map = {}
        sub_map = {}

        for item in category_data:
            cat = Category.objects.filter(slug=item["slug"]).first() or Category.objects.filter(name=item["name"]).first()
            if not cat:
                cat = Category.objects.create(name=item["name"], slug=item["slug"])
            else:
                cat.name = item["name"]
                cat.slug = item["slug"]
                cat.save()
            cat_map[item["slug"]] = cat

            for sub_name, sub_slug in item["subcategories"]:
                sub = Subcategory.objects.filter(category=cat, slug=sub_slug).first()
                if not sub:
                    sub = Subcategory.objects.create(category=cat, name=sub_name, slug=sub_slug)
                sub_map[f"{item['slug']}:{sub_slug}"] = sub

        # Styles
        styles_list = [
            ("Solitaire", "solitaire"),
            ("Halo", "halo"),
            ("Under Halo", "under-halo"),
            ("Diamond Shoulder", "diamond-shoulder"),
            ("Trilogy Three Stone", "three-stone"),
            ("Matching Set", "matching-set"),
            ("Traditional Court", "traditional-court"),
            ("Flat Court", "flat-court"),
            ("Soft Court", "soft-court"),
        ]
        for s_name, s_slug in styles_list:
            Style.objects.get_or_create(name=s_name, defaults={"slug": s_slug})

        # Sample Products
        sample_products = [
          {
            "name": "Classic Solitaire Diamond Ring",
            "category": "engagement-rings",
            "category_ref": cat_map.get("engagement-rings"),
            "subcategory_ref": sub_map.get("engagement-rings:solitaire"),
            "ring_style": "Solitaire",
            "description": "Exquisite 1.5 Carat Solitaire Engagement Ring set in 18ct White Gold.",
            "base_price": 250000.00,
            "discount_price": 225000.00,
            "total_stock": 10,
            "metal_type": "white-gold",
            "metal_karat": "18K",
            "diamond_cut": "round",
            "styles": ["Solitaire"],
            "is_featured": True,
            "is_active": True,
            "images": [
              "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=600&h=600&fit=crop"
            ]
          },
          {
            "name": "Emerald Cut Halo Ring",
            "category": "engagement-rings",
            "category_ref": cat_map.get("engagement-rings"),
            "subcategory_ref": sub_map.get("engagement-rings:halo"),
            "ring_style": "Halo",
            "description": "Stunning Emerald Cut Diamond Ring with pave halo border.",
            "base_price": 320000.00,
            "discount_price": None,
            "total_stock": 5,
            "metal_type": "platinum",
            "metal_karat": "950Pt",
            "diamond_cut": "emerald-cut",
            "styles": ["Halo"],
            "is_featured": True,
            "is_active": True,
            "images": [
              "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=600&h=600&fit=crop"
            ]
          },
          {
            "name": "Diamond Solitaire Stud Earrings",
            "category": "earrings",
            "category_ref": cat_map.get("earrings"),
            "subcategory_ref": sub_map.get("earrings:solitaire-studs"),
            "description": "Timeless 1.0 Carat total weight diamond stud earrings in Platinum.",
            "base_price": 180000.00,
            "discount_price": 165000.00,
            "total_stock": 12,
            "metal_type": "platinum",
            "metal_karat": "950Pt",
            "diamond_cut": "round",
            "earring_type": "studs",
            "is_featured": True,
            "is_active": True,
            "images": [
              "https://images.unsplash.com/photo-1630019852942-f89202989a59?w=600&h=600&fit=crop"
            ]
          },
          {
            "name": "Diamond Tennis Bracelet",
            "category": "bracelets",
            "category_ref": cat_map.get("bracelets"),
            "subcategory_ref": sub_map.get("bracelets:tennis-bracelets"),
            "description": "Elegant 5.0 Carat Diamond Tennis Bracelet crafted in 18ct White Gold.",
            "base_price": 450000.00,
            "discount_price": None,
            "total_stock": 4,
            "metal_type": "white-gold",
            "metal_karat": "18K",
            "diamond_cut": "round",
            "bracelet_type": "tennis",
            "is_featured": True,
            "is_active": True,
            "images": [
              "https://images.unsplash.com/photo-1611591475777-233cd73be328?w=600&h=600&fit=crop"
            ]
          }
        ]

        created_count = 0
        for data in sample_products:
            images = data.pop("images", [])
            style_names = data.pop("styles", [])
            product, created = Product.objects.get_or_create(name=data["name"], defaults=data)
            if created:
                created_count += 1
                for idx, img_url in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        url=img_url,
                        is_primary=(idx == 0)
                    )
                if style_names:
                    styles = [Style.objects.get_or_create(name=n)[0] for n in style_names]
                    product.styles.set(styles)

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded categories, subcategories, and {created_count} products."))
