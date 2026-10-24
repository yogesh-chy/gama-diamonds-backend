from django.db import migrations


def clean_filter_subcategories(apps, schema_editor):
    Subcategory = apps.get_model('products', 'Subcategory')
    # Remove filter-based or section-header items that are not actual product subcategories
    invalid_slugs = ['gold-colour', 'silver-colour', 'rose-gold', 'the-classics']
    Subcategory.objects.filter(slug__in=invalid_slugs).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_seed_all_dropdown_subcategories'),
    ]

    operations = [
        migrations.RunPython(clean_filter_subcategories, noop),
    ]
