from django.core.management.base import BaseCommand
from products.models import Category, Subcategory, Product, ProductImage, ProductSize, Style


class Command(BaseCommand):
    help = "Seeds initial sample jewellery products into the database"

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories and products...")

        # Create Categories
        rings_cat, _ = Category.objects.get_or_create(name="Rings")
        necklaces_cat, _ = Category.objects.get_or_create(name="Necklaces")
        bracelets_cat, _ = Category.objects.get_or_create(name="Bracelets")
        earrings_cat, _ = Category.objects.get_or_create(name="Earrings")

        # Sample Products
        sample_products = [
          {
            "name": "Classic Solitaire Diamond Ring",
            "category": "rings",
            "category_ref": rings_cat,
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
            "category": "rings",
            "category_ref": rings_cat,
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
            "category_ref": earrings_cat,
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
            "category_ref": bracelets_cat,
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

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} products."))
