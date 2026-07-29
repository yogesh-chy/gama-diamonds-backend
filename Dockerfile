FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# libpq-dev + gcc: needed to build psycopg2 against Postgres.
# netcat-openbsd: used by entrypoint.sh to wait for the db container.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
# Dev default — docker-compose.prod.yml overrides this with gunicorn.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
