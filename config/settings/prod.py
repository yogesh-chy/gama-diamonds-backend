import logging
from .base import *  # noqa: F401,F403
from .base import env

logger = logging.getLogger(__name__)

DEBUG = False

# Reverse proxy SSL header (essential for Render / Cloudflare / Envoy to avoid infinite redirect loop)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Allowed hosts: can be specified via env (comma-separated), defaults to render/railway domains and localhost
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[".onrender.com", ".railway.app", "localhost", "127.0.0.1", "*"]
)

import os
render_external_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_external_hostname and render_external_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_external_hostname)

# CSRF Trusted Origins for Django 4.0+
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["https://*.onrender.com", "https://*.railway.app", "https://*.vercel.app"]
)

if render_external_hostname:
    render_origin = f"https://{render_external_hostname}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

# Security headers
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# CORS configuration — sanitize trailing slashes to prevent corsheaders.E014
raw_cors_origins = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOWED_ORIGINS = [origin.rstrip("/") for origin in raw_cors_origins if origin]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
    r"^http://localhost:\d+$",
]
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)

# Ensure CORS origins are also trusted for CSRF
for origin in CORS_ALLOWED_ORIGINS:
    if origin and origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# Redis Cache for production rate limiting and shared state
if not env("REDIS_URL", default=None):
    logger.warning(
        "REDIS_URL not set in production. Using local memory cache. "
        "Provision a Redis instance on Render and set REDIS_URL for distributed rate limiting."
    )

# Email backend
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")

