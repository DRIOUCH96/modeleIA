# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm

ARG APP_VERSION=development

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MODEL_DIR=/app/model \
    APP_VERSION=${APP_VERSION} \
    HOME=/home/appuser

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /home/appuser appuser

# Cette couche ne sera reconstruite que si les dépendances changent.
COPY requirements-api.txt ./
RUN python -m pip install --no-cache-dir -r requirements-api.txt

# L’image n’embarque ni notebook, ni données, ni dépendances de test.
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup model/ ./model/

USER appuser

EXPOSE 8000

LABEL org.opencontainers.image.title="classifieur-films-api" \
      org.opencontainers.image.revision=${APP_VERSION}

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"]

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]