import os
import logging
from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


def auto_create_superuser(sender, **kwargs):
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
    if not email or not password:
        return

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if not user:
            logger.info("Creating initial superuser: %s", email)
            user = User.objects.create_superuser(email=email, password=password)
            user.is_email_verified = True
            user.save()
            logger.info("Superuser created successfully.")
        else:
            logger.info("Superuser %s exists. Syncing password & permissions...", email)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_email_verified = True
            user.save()
            logger.info("Superuser synced successfully.")
    except Exception as exc:
        logger.warning("Auto superuser creation skipped: %s", exc)


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        post_migrate.connect(auto_create_superuser, sender=self)
