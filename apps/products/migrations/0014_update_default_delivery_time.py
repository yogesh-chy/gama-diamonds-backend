from django.db import migrations, models


def update_delivery_time(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Product.objects.filter(
        models.Q(estimated_delivery_time__icontains="3-5")
        | models.Q(estimated_delivery_time="")
        | models.Q(estimated_delivery_time__isnull=True)
    ).update(estimated_delivery_time="14-15 Days")


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0013_add_dynamic_jewellery_dimensions"),
    ]

    operations = [
        migrations.RunPython(update_delivery_time, reverse_code=migrations.RunPython.noop),
    ]

