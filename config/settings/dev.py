from .base import *  # noqa: F401,F403
from .base import BASE_DIR, env

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Wide open in dev so the Next.js dev server never trips CORS while iterating.
CORS_ALLOW_ALL_ORIGINS = True

# Fall back to SQLite when DATABASE_URL isn't set, so a fresh clone runs
# with zero Postgres setup. Swap to real Postgres before the Week-1
# checkpoint so migrations/tests match production behavior.
if not env("DATABASE_URL", default=None):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Email backend: set to smtp.EmailBackend for real emails, or console.EmailBackend in .env if testing locally
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")

# If REDIS_URL isn't set, base.py falls back to per-process LocMemCache,
# which is fine for a single `runserver` process. If you're running
# multiple processes locally (e.g. via the Docker gunicorn command) set
# REDIS_URL=redis://localhost:6379/0 (docker-compose.yml's `redis` service)
# so OTP throttling/cooldowns behave the same as they will in prod.
