# Multi-stage Dockerfile for Cloud Platforms (Render, Railway, Fly.io) building from repo root
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app/backend:$PYTHONPATH"

COPY --from=builder /opt/venv /opt/venv

RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser \
    && mkdir -p /data \
    && chown -R appuser:appgroup /data /app

COPY --chown=appuser:appgroup backend /app/backend

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=3s --retries=5 --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
