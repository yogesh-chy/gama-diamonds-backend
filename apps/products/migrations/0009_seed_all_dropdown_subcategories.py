from django.db import migrations


def seed_complete_subcategories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Subcategory = apps.get_model('products', 'Subcategory')

    # Complete mapping matching the exact dropdown items from the navigation mega menus
    category_dropdown_map = {
        "engagement-rings": [
            ("Solitaire", "solitaire"),
            ("Halo", "halo"),
            ("Under Halo", "under-halo"),
            ("Diamond Shoulder", "diamond-shoulder"),
            ("Trilogy Three Stone", "three-stone"),
            ("Matching Set", "matching-set"),
        ],
        "wedding-rings": [
            ("Women's Plain", "womens-plain"),
            ("Eternity Rings", "eternity-rings"),
            ("Men's Plain", "mens-plain"),
            ("Men's Diamond", "mens-diamond"),
            ("Men's Pattern", "mens-pattern"),
            ("Traditional Court", "traditional-court"),
            ("Flat Court", "flat-court"),
            ("Soft Court", "soft-court"),
        ],
        "jewellery": [
            ("Earrings", "earrings"),
            ("Necklace", "necklace"),
            ("Statement Rings", "statement-rings"),
            ("Pendants", "pendants"),
            ("Bracelets & Bangles", "bracelets-bangles"),
            ("Gold Colour", "gold-colour"),
            ("Silver Colour", "silver-colour"),
            ("Rose Gold", "rose-gold"),
            ("Tennis Bracelets", "tennis-bracelets"),
            ("Solitaire Studs", "solitaire-studs"),
            ("Heart Pendants", "heart-pendants"),
            ("Cross Pendants", "cross-pendants"),
            ("Hoop Earrings", "hoop-earrings"),
            ("Hot Diamonds", "hot-diamonds"),
        ],
        "eternity-rings": [
            ("Full Eternity", "full-eternity"),
            ("Half Eternity", "half-eternity"),
            ("Seven Stone", "seven-stone"),
            ("Micro-Pave", "micro-pave"),
        ],
        "earrings": [
            ("Solitaire Studs", "solitaire-studs"),
            ("Hoop Earrings", "hoop-earrings"),
            ("Drop Earrings", "drop-earrings"),
            ("Halo Earrings", "halo-earrings"),
            ("Chandelier Earrings", "chandelier-earrings"),
        ],
        "necklaces": [
            ("Pendants", "pendants"),
            ("Heart Pendants", "heart-pendants"),
            ("Cross Pendants", "cross-pendants"),
            ("Tennis Necklaces", "tennis-necklaces"),
            ("Chains", "chains"),
        ],
        "bracelets": [
            ("Tennis Bracelets", "tennis-bracelets"),
            ("Bangles", "bangles"),
            ("Cuff Bracelets", "cuff-bracelets"),
            ("Chain Bracelets", "chain-bracelets"),
        ],
    }

    for cat_slug, subcategories in category_dropdown_map.items():
        cat = Category.objects.filter(slug=cat_slug).first()
        if not cat:
            cat = Category.objects.filter(name__iexact=cat_slug.replace("-", " ")).first()
        if not cat:
            continue

        for sub_name, sub_slug in subcategories:
            sub = Subcategory.objects.filter(category=cat, slug=sub_slug).first()
            if not sub:
                Subcategory.objects.create(
                    category=cat,
                    name=sub_name,
                    slug=sub_slug
                )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_seed_main_categories_subcategories'),
    ]

    operations = [
        migrations.RunPython(seed_complete_subcategories, noop),
    ]
