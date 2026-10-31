from django.db import models


class ContactInquiry(models.Model):
    INQUIRY_TYPES = [
        ("consultation", "Private Consultation"),
        ("bespoke", "Bespoke / Custom Design"),
        ("custom_jewellery", "Custom Jewellery Inquiry"),
        ("diamond_sourcing", "Diamond Sourcing Request"),
        ("suggestion", "Thought / Suggestion"),
        ("reach_out", "General Question / Reach Out"),
        ("newsletter", "Private Circle Newsletter"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted / In Progress"),
        ("resolved", "Resolved"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=50, blank=True, default="")
    subject = models.CharField(max_length=255, blank=True, default="")
    inquiry_type = models.CharField(max_length=50, choices=INQUIRY_TYPES, default="reach_out")
    message = models.TextField(blank=True, default="")
    timeframe = models.CharField(max_length=100, blank=True, default="")
    attachment_url = models.CharField(max_length=1000, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    admin_notes = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contact_inquiries"
        ordering = ["-created_at"]
        verbose_name = "Contact Inquiry & Form Submission"
        verbose_name_plural = "Contact Inquiries & Form Submissions"

    def __str__(self):
        title = self.subject or self.get_inquiry_type_display()
        sender = self.name or self.email
        return f"[{self.status.upper()}] {title} - {sender} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

