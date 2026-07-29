#!/bin/sh
set -e

if [ -n "$DATABASE_HOST" ]; then
  echo "Waiting for Postgres at ${DATABASE_HOST}:${DATABASE_PORT:-5432}..."
  until nc -z "$DATABASE_HOST" "${DATABASE_PORT:-5432}"; do
    sleep 0.5
  done
  echo "Postgres is up."
fi

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

exec "$@"
