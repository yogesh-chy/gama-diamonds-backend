import os
import sys

# Ensure apps directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

try:
    import django
    django.setup()
    from django.contrib.auth import get_user_model

    User = get_user_model()
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

    if email and password:
        if not User.objects.filter(email=email).exists():
            print(f"Creating superuser: {email}")
            user = User.objects.create_superuser(email=email, password=password)
            user.is_email_verified = True
            user.save()
            print("Superuser created successfully.")
        else:
            print(f"Superuser {email} already exists.")
    else:
        print("DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD not set. Skipping automatic superuser creation.")
except Exception as e:
    print(f"Superuser creation script encountered: {e}")
