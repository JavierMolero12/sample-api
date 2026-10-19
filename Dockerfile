# syntax=docker/dockerfile:1

# La imagen final es distroless python3-debian12, que trae Python 3.11:
# el builder usa la misma versión mayor y la misma base Debian (bookworm)
# para que las wheels compiladas (pydantic-core) sean compatibles.
ARG PYTHON_VERSION=3.11

# ---------- Etapa 1: dependencias ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Se copian primero los requirements para aprovechar la caché de capas:
# las dependencias solo se reinstalan si cambia requirements.txt.
COPY requirements.txt .
RUN pip install --target /build/deps -r requirements.txt

COPY app/ ./app/

# Precompila el bytecode aquí porque en Kubernetes el root filesystem es de solo lectura.
RUN python -m compileall -q /build/deps /build/app

# ---------- Etapa 2: runtime ----------
# distroless: sin shell, sin gestor de paquetes y con usuario nonroot (UID 65532).
# Menos superficie de ataque y menos CVEs que reportará Trivy.
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime

ARG APP_VERSION=dev

ENV PYTHONPATH=/app/deps \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION} \
    PORT=8080

WORKDIR /app

COPY --from=builder --chown=65532:65532 /build/deps /app/deps
COPY --from=builder --chown=65532:65532 /build/app /app/app

USER 65532:65532

EXPOSE 8080

# El ENTRYPOINT de la imagen distroless ya es /usr/bin/python3.
CMD ["-m", "app"]
