from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# No wildcard fallback in prod — fail loudly at boot if this isn't set,
# rather than silently accepting Host-header spoofing.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# No wildcard, no dev fallback — must be the exact Next.js production origin(s).
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_ALL_ORIGINS = False

# Required in prod: without REDIS_URL, base.py silently falls back to
# per-process LocMemCache and every gunicorn worker enforces OTP
# throttling/cooldowns independently of the others — see base.py CACHES
# comment. Fail at boot rather than let that ship unnoticed.
if not env("REDIS_URL", default=None):
    raise RuntimeError(
        "REDIS_URL must be set in production — required for shared OTP "
        "throttling/cooldown state across gunicorn workers/instances."
    )

# Real transactional email backend for OTP delivery. SMTP works with any
# provider (SES, Postmark, SendGrid, Mailgun, etc.) — set EMAIL_HOST /
# EMAIL_HOST_USER / EMAIL_HOST_PASSWORD via env. Swap to a provider-specific
# API backend later if SMTP throughput/deliverability becomes a bottleneck.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
