from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import EmailOTP


class Command(BaseCommand):
    """
    Deletes old EmailOTP rows so the table stays small and cheap to index.

    Not wired to run automatically anywhere in this MVP (no Celery beat /
    cron configured yet) — run it manually or via your platform's
    scheduled-job feature (Render Cron Job, Railway Cron, a k8s CronJob,
    etc.), e.g. daily:

        python manage.py purge_expired_otps

    Keeps rows around for a short grace period after expiry (default 7
    days) rather than deleting the instant they expire, so recently-expired
    codes are still visible in Django Admin for abuse investigation.
    """

    help = "Delete EmailOTP rows past their grace period (default: expired more than 7 days ago)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--grace-days",
            type=int,
            default=7,
            help="Keep expired OTP rows for this many days after expiry before deleting them.",
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["grace_days"])
        deleted, _ = EmailOTP.objects.filter(expires_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired OTP row(s) older than {cutoff.isoformat()}."))
