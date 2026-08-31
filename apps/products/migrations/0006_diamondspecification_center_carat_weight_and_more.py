import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_migrate_products_to_variants'),
    ]

    operations = [
        migrations.AddField(
            model_name='diamondspecification',
            name='center_carat_weight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='diamondspecification',
            name='diamond_origin',
            field=models.CharField(choices=[('lab_grown', 'Lab Grown'), ('natural', 'Natural')], default='lab_grown', max_length=20),
        ),
        migrations.AddField(
            model_name='diamondspecification',
            name='total_carat_weight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='metal_weight_grams',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='metal_karat',
            field=models.CharField(blank=True, choices=[('9K', '9ct'), ('10K', '10ct'), ('14K', '14ct'), ('18K', '18ct'), ('22K', '22ct'), ('24K', '24ct'), ('950Pt', '950 Platinum'), ('925Ag', '925 Silver')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='productvariant',
            name='metal_karat',
            field=models.CharField(blank=True, choices=[('9K', '9ct'), ('10K', '10ct'), ('14K', '14ct'), ('18K', '18ct'), ('22K', '22ct'), ('24K', '24ct'), ('950Pt', '950 Platinum'), ('925Ag', '925 Silver')], default='', max_length=20),
        ),
    ]