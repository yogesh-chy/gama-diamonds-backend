from django.db import models


class WebhookEvent(models.Model):
    """A processed Razorpay webhook, retained for idempotency and auditing."""

    event_type = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100)
    razorpay_order_id = models.CharField(max_length=100, blank=True, default="")
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("event_type", "razorpay_payment_id"),
                name="unique_webhook_event_per_payment",
            )
        ]
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.event_type}: {self.razorpay_payment_id}"
