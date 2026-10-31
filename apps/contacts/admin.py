from django.contrib import admin
from .models import ContactInquiry


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "inquiry_type",
        "name",
        "email",
        "phone",
        "subject",
        "status",
        "created_at",
    ]
    list_filter = ["inquiry_type", "status", "created_at"]
    search_fields = ["name", "email", "phone", "subject", "message", "admin_notes"]
    readonly_fields = ["created_at", "updated_at", "ip_address"]
    list_editable = ["status"]
    date_hierarchy = "created_at"
    actions = ["mark_as_contacted", "mark_as_resolved"]

    fieldsets = (
        ("Client Details", {
            "fields": ("name", "email", "phone", "ip_address")
        }),
        ("Inquiry Information", {
            "fields": ("inquiry_type", "subject", "message", "timeframe", "attachment_url")
        }),
        ("Status & Workflow", {
            "fields": ("status", "admin_notes", "created_at", "updated_at")
        }),
    )

    @admin.action(description="Mark selected inquiries as Contacted")
    def mark_as_contacted(self, request, queryset):
        queryset.update(status="contacted")

    @admin.action(description="Mark selected inquiries as Resolved")
    def mark_as_resolved(self, request, queryset):
        queryset.update(status="resolved")

