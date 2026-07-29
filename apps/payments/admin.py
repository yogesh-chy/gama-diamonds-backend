from django.contrib import admin

from .models import WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    """Read-only audit trail — useful when a payment dispute or a
    'why didn't my order update' support ticket needs investigating."""
    list_display = ("event_type", "razorpay_payment_id", "razorpay_order_id", "received_at")
    list_filter = ("event_type",)
    search_fields = ("razorpay_payment_id", "razorpay_order_id")
    readonly_fields = ("event_type", "razorpay_payment_id", "razorpay_order_id", "payload", "received_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
