FROM node:22-slim AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json frontend/
RUN --mount=type=bind,source=despliegue/casa,target=/tmp/casa \
    cat /tmp/casa/certificados/*.crt > /tmp/extra.pem 2>/dev/null || true; \
    if [ -s /tmp/extra.pem ]; then export NODE_EXTRA_CA_CERTS=/tmp/extra.pem; fi; \
    npm --prefix frontend ci --include=dev
COPY . .
RUN npm --prefix frontend run build

FROM python:3.11-slim

RUN --mount=type=bind,source=despliegue/casa,target=/tmp/casa \
    if ls /tmp/casa/certificados/*.crt >/dev/null 2>&1; then \
      cp /tmp/casa/certificados/*.crt /usr/local/share/ca-certificates/ \
      && update-ca-certificates; \
    fi

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY --from=frontend /app/frontend/dist frontend/dist

RUN useradd --create-home --uid 1000 app \
    && mkdir -p media staticfiles \
    && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["sh", "scripts/start-web.sh"]
