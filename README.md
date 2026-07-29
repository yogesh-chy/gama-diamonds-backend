# Jewelry Store Backend

Django + DRF backend. This drop implements the **full folder structure** from
the TRD and a **complete, production-hardened OTP (passwordless) login
flow**: a shopper enters only their email, gets a 6-digit code, and
verifying it logs them in — creating the account silently on first use, so
there's no separate "register" step. `products/`, `orders/`, `payments/`
are scaffolded (empty urls, apps.py, models.py stubs) so the project runs
end-to-end today, ready for Weeks 1–3 of the execution plan.

## Setup — Docker (recommended)

```bash
cp .env.example .env   # edit SECRET_KEY at minimum
docker compose up --build
```

That's it — this brings up Postgres, Redis, and the Django app together,
waits for Postgres/Redis to actually accept connections (not just
"container started"), runs migrations automatically, and serves on
`http://localhost:8000`. Redis backs OTP throttling and resend-cooldown
state — see "OTP login" below for why that needs to be shared, not
per-process. `docker-compose.yml` points the app at the `db`/`redis`
services by container name, overriding whatever `DATABASE_URL`/`REDIS_URL`
you have in `.env` — so the same `.env` works whether you run this way or
bare-metal.

```bash
# Create an admin user (run once, container must be up)
docker compose exec web python manage.py createsuperuser

# Run the test suite
docker compose exec web pytest apps/accounts/

# Tear down (add -v to also wipe the Postgres volume)
docker compose down
```

To try a production-like run locally (gunicorn instead of the dev server,
`config.settings.prod`, no live code reload):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### Setup — bare metal (no Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit SECRET_KEY at minimum
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Dev settings fall back to SQLite automatically if `DATABASE_URL` isn't set
(and you're not using Docker) — switch to real Postgres before the Week-1
checkpoint so migrations/tests match production. Same story for
`REDIS_URL`: unset, dev falls back to Django's per-process `LocMemCache`,
which is fine for one `runserver` process but will NOT correctly enforce
OTP throttling/cooldowns across multiple processes (see "OTP login" below)
— set `REDIS_URL` before load-testing or deploying.

## OTP login (`/api/auth/otp/`)

There's no password anywhere in the shopper-facing flow. One endpoint
requests a code, one verifies it:

1. `POST /otp/request/ {"email": "..."}` → always `200`, generic message,
   regardless of whether the email has an account yet. The 6-digit code is
   emailed (or, in dev, printed to the runserver console via the console
   email backend — no SMTP setup needed to test the flow locally).
2. `POST /otp/verify/ {"email": "...", "code": "123456"}` → on a valid code,
   gets-or-creates the `User` for that email (first-ever verification for
   an email *is* signup) and returns `{ access, refresh, user }` — the same
   shape the old password-based `/login/` returned, so the frontend's
   `user.is_staff` redirect logic didn't need to change.

Security properties worth knowing about, all enforced in
`accounts/services.py`:
- Codes are hashed (SHA-256 + `SECRET_KEY` pepper) before hitting the
  database — a DB leak doesn't hand out live, usable codes.
- Wrong-code guesses are capped (`OTP_MAX_ATTEMPTS`, default 5) before the
  code is invalidated outright, independent of how fast the guesses come in.
- Requesting a new code invalidates any still-live code for that email, so
  only the most recently sent one ever works.
- A resend cooldown (`OTP_RESEND_COOLDOWN_SECONDS`, default 60s) and two
  separate throttle scopes — per-IP (`otp_request`) and per-*email*
  (`otp_request_email`) — stop both "one IP spraying many inboxes" and "one
  inbox getting spammed from rotating IPs."
- `/otp/request/` never reveals whether the email has an account — the
  response is identical either way, so it can't be used to enumerate
  registered users.

`OTP_LENGTH` / `OTP_EXPIRY_MINUTES` / `OTP_MAX_ATTEMPTS` /
`OTP_RESEND_COOLDOWN_SECONDS` are all env-overridable (see `.env.example`)
if you want to tune them later without a code change.

## Auth endpoints (`/api/auth/`)

| Method | Endpoint | Auth | Notes |
|---|---|---|---|
| POST | `/otp/request/` | Public | rate-limited (10/hour/IP + 3/hour/email); always 200, generic message |
| POST | `/otp/verify/` | Public | rate-limited (20/hour/IP); creates the user on first success, returns `access`, `refresh`, `user` (incl. `is_staff`) |
| POST | `/token/refresh/` | Refresh token | rotates + blacklists the old refresh token |
| POST | `/logout/` | Access token | blacklists the given refresh token |
| GET/PATCH | `/me/` | Access token | view/update profile |
| GET/POST | `/addresses/` | Access token | list/create, scoped to the caller |
| GET/PATCH/DELETE | `/addresses/{id}/` | Access token | 404s (not 403) on another user's address |

## Key architectural decisions (and why)

- **Single `User` model, `is_staff` flag** — shoppers and the platform owner
  share one auth path (JWT issuance, OTP verification, permissions). No
  separate tables to keep in sync, no extra join on every authenticated
  request.
- **No password for shopper accounts** — `get_or_create_for_otp_login()`
  (`accounts/managers.py`) creates new users with `set_unusable_password()`.
  Proving control of the inbox via OTP *is* the account's only credential;
  there's nothing to leak, reuse across sites, or reset.
- **Refresh token rotation + blacklist** (`ROTATE_REFRESH_TOKENS` +
  `BLACKLIST_AFTER_ROTATION` in `config/settings/base.py`) — a leaked
  refresh token is only usable once; the moment the real client refreshes,
  the old one is dead. `/logout/` blacklists on demand too.
- **`is_staff` embedded as a JWT claim** — lets frontend route-guard
  middleware (Phase 2 admin dashboard) check admin status off the token
  itself. This is a UX shortcut only: every admin-only endpoint still must
  enforce `IsAdminUser` server-side, since a claim baked into an
  already-issued token can't reflect a staff-status change until the token
  expires (≤15 min) or the user logs in again.
- **Double ownership enforcement on Address** — `get_queryset()` filters to
  `request.user` (so another user's address never appears in a list) *and*
  `IsOwner.has_object_permission` blocks direct access by id. Returns 404,
  not 403, so a user can't even confirm another user's address id exists.
- **One default address per user, enforced in `Address.save()`** — not just
  in the serializer, so Django Admin edits and any future direct ORM writes
  (e.g. checkout auto-selecting a default) can't leave two rows marked
  default under concurrent requests.
- **OTP codes hashed, single-use, attempt-capped, IP+email throttled** — see
  "OTP login" above; the short version is every layer of the OWASP OTP
  guidance is covered without adding new infrastructure beyond Redis (which
  the throttles already needed).
- **Redis-backed cache (`django-redis`)** — required in prod
  (`config/settings/prod.py` raises at boot without `REDIS_URL`). Django's
  default per-process `LocMemCache` would let every gunicorn worker
  (`docker-compose.prod.yml` runs `--workers 3`) enforce its own throttle
  counters and OTP cooldowns independently, silently multiplying every
  rate limit by the worker count. This was true for the throttles even
  before OTP existed — Redis fixes it for both.
- **`core/exceptions.py` custom exception handler** — normalizes every
  error response (validation, auth, throttling, 500) into one
  `{ "error": { "code", "message", "details" } }` shape, so the Next.js
  frontend has a single error-handling branch instead of one per failure
  type.
- **Settings split (`base` / `dev` / `prod`)** — `prod.py` has no wildcard
  fallbacks for `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, or `REDIS_URL`; it
  fails at boot if they're missing rather than silently running insecurely
  or with per-process rate limits.

## Secrets

Every credential (`SECRET_KEY`, `POSTGRES_PASSWORD`, Razorpay keys, SMTP
creds) lives in `.env`, which is git-ignored — `docker-compose.yml` reads
them via `${VARIABLE}` substitution rather than hardcoding anything.
`.env.example` is the only one meant to be committed, and it contains
placeholders only. Before your first commit, double-check `git status`
doesn't show `.env`.

In real production (Render/Railway/etc.), you won't use this compose
file's Postgres/Redis credentials at all — use the platform's managed
Postgres and managed Redis add-ons, which generate their own, and copy
those into that platform's environment-variable dashboard as
`DATABASE_URL` / `REDIS_URL`. For email, use your provider's SMTP creds
(SES, Postmark, SendGrid, Mailgun, etc.) as `EMAIL_HOST`/`EMAIL_HOST_USER`/
`EMAIL_HOST_PASSWORD`.

## Deployment

Don't self-host production on a local/on-prem machine — Razorpay's webhook
(TRD Section 6, step 7) needs a stable public HTTPS endpoint, which a
residential connection/NAT can't reliably provide, and you'd also be on the
hook for your own backups, patching, and uptime.

This same `Dockerfile` is deployable as-is to Render, Railway, Fly.io, or
DigitalOcean App Platform — all of them build directly from a `Dockerfile`
and offer managed Postgres and Redis add-ons. Point the platform's build at
this repo, add managed Postgres + Redis instances, set `DATABASE_URL` /
`REDIS_URL` (from those add-ons) plus the rest of `.env.example` as
environment variables in the platform's dashboard, and set
`DJANGO_SETTINGS_MODULE=config.settings.prod`. Happy to write the
platform-specific config (`render.yaml` / Railway service config) once
you've picked one.

## Recommended before real production traffic (not in MVP scope, flagging for later)

- **Move OTP email sending to a background task (Celery + the same Redis
  as broker).** Right now `accounts/services.send_otp_email()` is
  synchronous — a slow/hung SMTP call blocks the request for up to
  `EMAIL_TIMEOUT` seconds, and a provider outage turns *every* login into a
  failure at once. Fine at MVP traffic, worth decoupling once concurrent
  logins are common.
- **`purge_expired_otps` isn't scheduled anywhere yet** — run it via your
  platform's cron/scheduled-job feature (Render Cron Job, Railway Cron, a
  k8s CronJob, etc.), e.g. daily, so `email_otps` doesn't grow unbounded.
- **SMS OTP as a fallback channel**, if email deliverability turns out to
  be inconsistent in practice (spam folders, corporate mail filters) — the
  `EmailOTP.purpose` field and `services.py` structure are already set up
  to add a second `Purpose`/channel without reworking the flow.
- A short "did you mean...?" client-side email-typo check (frontend, not
  backend) — with no password step, a mistyped email silently sends
  someone else's inbox a code instead of surfacing a wrong-password error.

## Tests

```bash
pytest apps/accounts/
```

Covers: OTP request (email sent, no user-existence leakage, invalid email
rejected, resend cooldown enforced, a new request invalidates the previous
code), OTP verify (correct code creates a user and returns tokens, a
returning email gets 200 not 201, wrong codes are rejected and counted,
`OTP_MAX_ATTEMPTS` locks the code even to the correct value afterward,
expired codes are rejected, correct `is_staff` in the response for both
shopper and admin), token refresh, logout blacklisting + reuse rejection,
`/me/`, and address CRUD — including that user A can never read, update, or
delete user B's address.

Run the full suite (all apps) with:

```bash
pytest
```
