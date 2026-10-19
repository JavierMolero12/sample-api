import socket

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_returns_ok():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_info_exposes_version_hostname_and_environment(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "abc1234")
    monkeypatch.setenv("APP_ENV", "test")

    response = client.get("/api/v1/info")

    assert response.status_code == 200
    assert response.json() == {
        "app": "sample-api",
        "version": "abc1234",
        "hostname": socket.gethostname(),
        "environment": "test",
    }


def test_metrics_use_prometheus_format_and_route_templates():
    client.get("/api/v1/info")

    response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert (
        'sample_api_http_requests_total{method="GET",route="/api/v1/info",status="200"}'
        in response.text
    )
    assert "sample_api_http_request_duration_seconds_bucket" in response.text


def test_unknown_routes_are_grouped_to_limit_cardinality():
    assert client.get("/does-not-exist").status_code == 404

    metrics = client.get("/api/v1/metrics").text

    assert 'route="unmatched",status="404"' in metrics
    assert "/does-not-exist" not in metrics
