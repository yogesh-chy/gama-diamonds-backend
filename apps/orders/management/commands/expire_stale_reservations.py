from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Order


class Command(BaseCommand):
    """
    Marks pending_payment orders whose checkout reservation has lapsed as
    'expired'. NOT required for correctness — orders/services.py already
    ignores expired reservations when checking available stock for a new
    checkout, and payments/views.py still accepts a late payment on an
    'expired' order. This command is pure housekeeping, so abandoned
    checkouts don't sit as 'pending_payment' forever in Django Admin /
    order history.

    Safe to run repeatedly. Schedule it every 5-10 minutes via cron, a
    Render/Railway Cron Job, or similar — no Celery/task queue required
    for this.
    """
    help = "Marks lapsed checkout reservations as 'expired'."

    def handle(self, *args, **options):
        updated = Order.objects.filter(
            status="pending_payment",
            reservation_expires_at__lt=timezone.now(),
        ).update(status="expired")
        self.stdout.write(self.style.SUCCESS(f"Expired {updated} stale order(s)."))
