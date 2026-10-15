# Kontekst: loyiha ildizi (docker-compose.yml da context: .)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
# CPU uchun PyTorch (GPU kerak bo‘lsa, index-url ni CUDA versiyasiga almashtiring)
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r /tmp/requirements.txt

COPY ai/kltool /app/kltool
COPY backend /app

RUN useradd --create-home --uid 10001 app && mkdir -p /data /models && chown -R app /data
USER app

ENV BT_DATABASE_URL=sqlite:////data/bogimtahlil.db \
    BT_STORAGE_DIR=/data/storage \
    BT_MODEL_PATH=/models/model.pt

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
