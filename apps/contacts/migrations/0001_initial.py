# Generated migration for contacts app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ContactInquiry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, default="", max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, default="", max_length=50)),
                ("subject", models.CharField(blank=True, default="", max_length=255)),
                (
                    "inquiry_type",
                    models.CharField(
                        choices=[
                            ("consultation", "Private Consultation"),
                            ("bespoke", "Bespoke / Custom Design"),
                            ("custom_jewellery", "Custom Jewellery Inquiry"),
                            ("diamond_sourcing", "Diamond Sourcing Request"),
                            ("suggestion", "Thought / Suggestion"),
                            ("reach_out", "General Question / Reach Out"),
                            ("newsletter", "Private Circle Newsletter"),
                            ("other", "Other"),
                        ],
                        default="reach_out",
                        max_length=50,
                    ),
                ),
                ("message", models.TextField(blank=True, default="")),
                ("timeframe", models.CharField(blank=True, default="", max_length=100)),
                (
                    "attachment_url",
                    models.CharField(blank=True, default="", max_length=1000),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("contacted", "Contacted / In Progress"),
                            ("resolved", "Resolved"),
                            ("archived", "Archived"),
                        ],
                        default="new",
                        max_length=20,
                    ),
                ),
                ("admin_notes", models.TextField(blank=True, default="")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Contact Inquiry & Form Submission",
                "verbose_name_plural": "Contact Inquiries & Form Submissions",
                "db_table": "contact_inquiries",
                "ordering": ["-created_at"],
            },
        ),
    ]

