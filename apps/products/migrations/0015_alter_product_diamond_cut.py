from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0014_update_default_delivery_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='diamond_cut',
            field=models.CharField(
                blank=True,
                choices=[
                    ('round', 'Round Brilliant'),
                    ('princess', 'Princess'),
                    ('oval', 'Oval'),
                    ('pear', 'Pear'),
                    ('cushion', 'Cushion'),
                    ('emerald-cut', 'Emerald'),
                    ('radiant', 'Radiant Cut'),
                    ('marquise', 'Marquise'),
                    ('asscher', 'Asscher'),
                    ('heart', 'Heart'),
                    ('plain', 'Plain / No Diamond'),
                ],
                max_length=30,
                null=True,
            ),
        ),
    ]

