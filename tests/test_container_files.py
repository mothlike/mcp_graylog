from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_runs_streamable_http_and_healthchecks_mcp_path():
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "mcp-graylog" in dockerfile
    assert "--transport" in dockerfile
    assert "streamable-http" in dockerfile
    assert "--host" in dockerfile
    assert "0.0.0.0" in dockerfile
    assert "--port" in dockerfile
    assert "8000" in dockerfile
    assert "--path" in dockerfile
    assert "/mcp" in dockerfile
    assert "socket.create_connection(('127.0.0.1', 8000)" in dockerfile
    assert "/health_check" not in dockerfile
    assert "requests" not in dockerfile


def test_entrypoint_requires_graylog_endpoint_and_supported_auth():
    entrypoint = (ROOT / "entrypoint.sh").read_text()

    assert "#!/bin/sh" in entrypoint
    assert "set -eu" in entrypoint
    assert "GRAYLOG_ENDPOINT is required" in entrypoint
    assert "GRAYLOG_TOKEN" in entrypoint
    assert "GRAYLOG_USERNAME" in entrypoint
    assert "GRAYLOG_PASSWORD" in entrypoint
    assert (
        "GRAYLOG_TOKEN or GRAYLOG_USERNAME/GRAYLOG_PASSWORD is required"
        in entrypoint
    )
    assert 'exec "$@"' in entrypoint
    assert "python -m mcp_graylog.server" not in entrypoint


def test_docker_compose_uses_explicit_env_without_insecure_defaults():
    compose = (ROOT / "docker-compose.yml").read_text()

    assert "GRAYLOG_ENDPOINT: ${GRAYLOG_ENDPOINT}" in compose
    assert "GRAYLOG_TOKEN: ${GRAYLOG_TOKEN}" in compose
    assert "GRAYLOG_VERIFY_SSL: ${GRAYLOG_VERIFY_SSL:-true}" in compose
    assert "GRAYLOG_TIMEOUT: ${GRAYLOG_TIMEOUT:-30}" in compose
    assert "MCP_SERVER_DNS_REBINDING_PROTECTION" in compose
    assert "MCP_SERVER_ALLOWED_HOSTS" in compose
    assert "MCP_SERVER_ALLOWED_ORIGINS" in compose
    assert "admin" not in compose
    assert "mock-graylog" not in compose
    assert "./logs" not in compose
