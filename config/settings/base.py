import sys
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "apps"))

env = environ.Env()
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-prod")
DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",

    # local apps
    "core",
    "accounts",
    "products",
    "orders",
    "payments",
]

try:
    import whitenoise  # noqa: F401
    HAS_WHITENOISE = True
except ImportError:
    HAS_WHITENOISE = False

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    *(["whitenoise.middleware.WhiteNoiseMiddleware"] if HAS_WHITENOISE else []),
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://postgres:postgres@localhost:5432/jewelry_store",
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if HAS_WHITENOISE
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Cloudinary Configuration
# ---------------------------------------------------------------------------
CLOUDINARY_CLOUD_NAME = env("CLOUDINARY_CLOUD_NAME", default="")
CLOUDINARY_API_KEY = env("CLOUDINARY_API_KEY", default="")
CLOUDINARY_API_SECRET = env("CLOUDINARY_API_SECRET", default="")
CLOUDINARY_URL = env("CLOUDINARY_URL", default="")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Locked down by default — every new endpoint is private unless a view
    # explicitly opts into AllowAny (register/login do this).
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "120/minute",
        # Scoped throttles used only by accounts.throttles (OTP login) —
        # tighter than the global anon rate because these two endpoints are
        # the direct target of enumeration/spam-inbox/brute-force bots.
        # Two layers on the "request OTP" step on purpose:
        #   otp_request        — coarse per-IP ceiling (stop one IP from
        #                        spamming OTPs to many different emails)
        #   otp_request_email  — tight per-email ceiling (stop anyone,
        #                        from any/rotating IPs, from spamming one
        #                        inbox / running up your email-provider bill)
        # otp_verify is deliberately looser than the old "login" rate would
        # suggest, because the *real* brute-force guard on guessing a code
        # is OTP_MAX_ATTEMPTS in accounts/services.py (5 wrong guesses and
        # the code itself is dead) — this throttle just stops a fast script
        # from burning through many different OTP records back-to-back.
        "otp_request": "10/hour",
        "otp_request_email": "3/hour",
        "otp_verify": "20/hour",
    },
}

# ---------------------------------------------------------------------------
# Simple JWT
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Rotation + blacklist-after-rotation means a stolen refresh token is
    # only useful once — the moment the legitimate client refreshes, the
    # old token is dead. This is the single highest-value anti-replay
    # control for a JWT setup and costs nothing to turn on.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------------------------------------------------------------------------
# CORS — restricted to the known Next.js origin(s), per TRD Section 7
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Razorpay — no defaults for the two secrets on purpose. Empty string lets
# the app boot in dev before you've set up a Razorpay test account, but
# payments/razorpay_client.py and signature.py will fail loudly (auth
# error / signature mismatch) rather than silently using a wrong secret.
# ---------------------------------------------------------------------------
RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")
RAZORPAY_WEBHOOK_SECRET = env("RAZORPAY_WEBHOOK_SECRET", default="")

# How long a checkout holds its items against other users' checkouts
# before the hold lapses and the stock becomes available to them again.
# See orders/services.py (_reserved_quantity, checkout_cart).
CHECKOUT_RESERVATION_MINUTES = env.int("CHECKOUT_RESERVATION_MINUTES", default=15)

# ---------------------------------------------------------------------------
# Cache — backs DRF throttling (register/login/otp scopes) AND the OTP
# resend-cooldown key in accounts/services.py.
#
# Why this matters: gunicorn runs multiple worker *processes*
# (docker-compose.prod.yml uses --workers 3), and any real deployment will
# eventually run more than one app instance behind a load balancer. Django's
# default LOCMEM cache is per-process, in-memory, not shared. With LOCMEM,
# a "5 requests/hour" throttle is actually "5 requests/hour, per worker" —
# an attacker (or a flaky frontend retry loop) effectively gets
# rate_limit * worker_count. Same bug would hit the OTP resend-cooldown: a
# user could get a fresh OTP every request just by getting round-robined
# across workers. Redis fixes this by giving every process the same view
# of throttle/cooldown state. This was silently wrong even before OTP was
# added (register/login throttles), so fixing it here fixes both.
# ---------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default=None)

if REDIS_URL and not REDIS_URL.startswith("redis://localhost") and not REDIS_URL.startswith("redis://127.0.0.1"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
        }
    }
else:
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }

# ---------------------------------------------------------------------------
# Email — used exclusively for OTP delivery (accounts/services.py). Console
# backend in dev (see dev.py) prints the OTP to the runserver log instead of
# sending real mail. Point these at a transactional provider (SES, Postmark,
# SendGrid SMTP, etc.) in prod — see prod.py.
# ---------------------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Gama Diamonds <no-reply@gamadiamonds.example>")
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)  # seconds — never let a slow SMTP call hang the request

# ---------------------------------------------------------------------------
# OTP login (replaces password auth entirely — see accounts/services.py,
# accounts/views.py). One flow serves both signup and login: a first-time
# email gets an account created for it silently on successful verification,
# matching the "just enter your email" UX of the reference site.
# ---------------------------------------------------------------------------
OTP_LENGTH = env.int("OTP_LENGTH", default=6)
OTP_EXPIRY_MINUTES = env.int("OTP_EXPIRY_MINUTES", default=5)
OTP_MAX_ATTEMPTS = env.int("OTP_MAX_ATTEMPTS", default=5)          # wrong-code guesses before the code is dead
OTP_RESEND_COOLDOWN_SECONDS = env.int("OTP_RESEND_COOLDOWN_SECONDS", default=60)  # min gap between two sends to the same email

# ---------------------------------------------------------------------------
# API docs (drf-spectacular)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Jewelry Store API",
    "DESCRIPTION": "Backend API for the online jewelry store (auth, catalog, cart, orders, payments).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
