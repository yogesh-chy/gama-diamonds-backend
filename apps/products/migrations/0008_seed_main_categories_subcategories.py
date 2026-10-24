from django.db import migrations


def seed_categories_and_subcategories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Subcategory = apps.get_model('products', 'Subcategory')
    Style = apps.get_model('products', 'Style')

    # Seed Styles
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
    for name, slug in styles_list:
        Style.objects.get_or_create(name=name, defaults={"slug": slug})

    # Main categories and their dropdown / structural subcategories
    # (Note: Shapes like Round, Princess, Cushion, Oval, Pear, Emerald, Marquise, Radiant, Asscher
    # are SKIPPED as subcategories because products are filtered/shown by their shape attribute)
    data = [
        {
            "name": "Engagement Rings",
            "slug": "engagement-rings",
            "aliases": ["Rings"],
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
            "aliases": ["Wedding Bands", "Wedding"],
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
            "aliases": ["Eternity Bands", "Eternity"],
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
            "aliases": [],
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
            "aliases": ["Necklaces"],
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
            "aliases": ["Bracelets & Bangles"],
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
            "aliases": ["Fine Jewellery"],
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

    for item in data:
        cat = Category.objects.filter(slug=item["slug"]).first()
        if not cat:
            for alias in item["aliases"]:
                cat = Category.objects.filter(name__iexact=alias).first()
                if cat:
                    break

        if not cat:
            cat, _ = Category.objects.get_or_create(
                name=item["name"],
                defaults={"slug": item["slug"]}
            )
        else:
            cat.name = item["name"]
            cat.slug = item["slug"]
            cat.save()

        # Seed subcategories
        for sub_name, sub_slug in item["subcategories"]:
            sub = Subcategory.objects.filter(category=cat, slug=sub_slug).first()
            if not sub:
                Subcategory.objects.get_or_create(
                    category=cat,
                    name=sub_name,
                    defaults={"slug": sub_slug}
                )


def remove_categories_and_subcategories(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_remove_productvariant_unique_product_variant_combination_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_categories_and_subcategories, remove_categories_and_subcategories),
    ]
