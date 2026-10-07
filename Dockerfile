FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_DEBUG=0
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libjpeg62-turbo zlib1g && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd -m begoyim && mkdir -p /app/media /app/staticfiles && chown -R begoyim /app/media /app/staticfiles
USER begoyim

EXPOSE 8000
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py seed_demo ${SEED_ARGS:---reference-only} && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60"]
