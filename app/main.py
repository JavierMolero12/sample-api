"""sample-api: microservicio de ejemplo para el flujo GitOps."""

import os
import socket
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

APP_NAME = "sample-api"

REQUESTS_TOTAL = Counter(
    "sample_api_http_requests_total",
    "Total de peticiones HTTP atendidas.",
    ["method", "route", "status"],
)
REQUEST_DURATION = Histogram(
    "sample_api_http_request_duration_seconds",
    "Latencia de las peticiones HTTP en segundos.",
    ["method", "route"],
)

app = FastAPI(title=APP_NAME, version=os.getenv("APP_VERSION", "dev"))


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    # Se etiqueta con la plantilla de la ruta (p. ej. /api/v1/info) y no con la URL
    # real: así las rutas inexistentes no disparan la cardinalidad de las series.
    route = request.scope.get("route")
    route_path = getattr(route, "path", "unmatched")
    REQUEST_DURATION.labels(request.method, route_path).observe(time.perf_counter() - start)
    REQUESTS_TOTAL.labels(request.method, route_path, str(response.status_code)).inc()
    return response


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    # Endpoint ligero y sin dependencias externas: lo usan liveness y readiness.
    return {"status": "ok"}


@app.get("/api/v1/info")
def info() -> dict[str, str]:
    # Las variables se leen en cada petición para reflejar el entorno real del pod.
    return {
        "app": APP_NAME,
        "version": os.getenv("APP_VERSION", "dev"),
        "hostname": socket.gethostname(),
        "environment": os.getenv("APP_ENV", "local"),
    }


@app.get("/api/v1/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
