# MCP Graylog Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the Graylog MCP server into a current, Codex-friendly stdio MCP server with optional Streamable HTTP support, Graylog 6+ compatible Search Scripting API calls, safer authentication, and reproducible tests.

**Architecture:** Keep the MCP boundary thin and typed: `mcp_graylog/server.py` registers tools and delegates to focused domain modules. Move Graylog HTTP details into `mcp_graylog/graylog_client.py`, shared models into `mcp_graylog/models.py`, and entrypoint logic into `mcp_graylog/cli.py`. Codex uses stdio by default; HTTP is an explicit opt-in transport for remote/shared deployments. The Graylog adapter targets the Search Scripting API available in Graylog 6+ (`/api/search/messages` and `/api/search/aggregate`) rather than the legacy `/api/search/universal/*` endpoints.

**Tech Stack:** Python 3.11+, official `mcp[cli]` SDK `FastMCP`, `httpx`, Pydantic v2, `pydantic-settings`, pytest, ruff.

---

## File Structure

- Modify `pyproject.toml`: update runtime/dev dependencies, Python baseline, console script, ruff/pytest config.
- Modify `requirements.txt`: keep it aligned with runtime dependencies for Docker/simple installs.
- Modify `mcp_graylog/config.py`: replace global side-effect config with typed settings and safe auth modes.
- Create `mcp_graylog/models.py`: Pydantic request/response models for tool inputs and normalized Graylog outputs.
- Create `mcp_graylog/graylog_client.py`: modern Graylog API adapter using `/api/search/messages` and `/api/search/aggregate`.
- Modify `mcp_graylog/server.py`: register typed MCP tools only; no FastAPI app in the stdio module.
- Create `mcp_graylog/cli.py`: choose `stdio` by default and `streamable-http` only when requested.
- Modify `Dockerfile`: make Docker run HTTP MCP intentionally on `/mcp`.
- Modify `entrypoint.sh`: stop pretending stdio is HTTP; run the CLI with explicit transport.
- Modify `README.md`: document Codex stdio config first, remote HTTP second.
- Modify `DOCUMENTATION.md`: refresh the existing long-form reference or replace it with a concise current reference.
- Modify `env.example`: switch examples to access-token auth and explicit transport settings.
- Modify `examples/basic_usage.py`: update examples to the new typed tool input shape and Codex-first setup.
- Modify `example_setup.sh`: update shell setup to `GRAYLOG_TOKEN` and stdio defaults.
- Modify `test_cursor_integration.py`: remove stale Cursor/Docker/password guidance or convert it into current config generation.
- Create/modify tests under `tests/`: config, Graylog request building, MCP tool behavior, CLI transport selection.
- Remove after migration: `run_server.py`, `mcp_graylog/client.py` compatibility imports only if no tests or examples still import them.

---

### Task 1: Modernize Packaging And Test Harness

**Files:**
- Modify: `pyproject.toml`
- Modify: `requirements.txt`
- Test: `tests/test_packaging.py`

- [x] **Step 1: Write the failing dependency and entrypoint tests**

Create `tests/test_packaging.py`:

```python
from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_uses_official_mcp_sdk_and_httpx():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dependencies = data["project"]["dependencies"]

    assert "mcp[cli]>=1.13.0" in dependencies
    assert "httpx>=0.27.0" in dependencies
    assert all(not dep.startswith("fastmcp") for dep in dependencies)
    assert all(not dep.startswith("requests") for dep in dependencies)


def test_pyproject_exposes_mcp_graylog_console_script():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert data["project"]["scripts"]["mcp-graylog"] == "mcp_graylog.cli:main"


def test_requirements_match_runtime_dependencies():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    pyproject_deps = set(data["project"]["dependencies"])
    requirements = {
        line.strip()
        for line in (ROOT / "requirements.txt").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }

    assert requirements == pyproject_deps
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_packaging.py -q
```

Expected: FAIL because `pyproject.toml` still depends on `fastmcp`/`requests` and has no `mcp-graylog` console script.

- [x] **Step 3: Update package metadata**

Replace the dependency and tooling sections in `pyproject.toml` with:

```toml
[project]
name = "mcp-graylog"
version = "0.2.0"
description = "MCP server for Graylog integration"
authors = [
    {name = "MCP Graylog Team", email = "team@example.com"}
]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.13.0",
    "httpx>=0.27.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
mcp-graylog = "mcp_graylog.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.6.0",
    "mypy>=1.10.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

Replace `requirements.txt` with:

```text
mcp[cli]>=1.13.0
httpx>=0.27.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
python-dotenv>=1.0.0
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
./venv/bin/python -m pytest tests/test_packaging.py -q
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add pyproject.toml requirements.txt tests/test_packaging.py
git commit -m "chore: modernize mcp graylog package metadata"
```

---

### Task 2: Replace Global Config With Safe Settings

**Files:**
- Modify: `mcp_graylog/config.py`
- Test: `tests/test_config.py`

- [x] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
import pytest
from pydantic import SecretStr, ValidationError

from mcp_graylog.config import GraylogSettings


def test_token_auth_headers_mask_secret_value():
    settings = GraylogSettings(
        endpoint="https://graylog.example.test",
        token=SecretStr("token-value"),
    )

    headers = settings.auth_headers()
    assert headers["Authorization"].startswith("Basic ")
    assert "token-value" not in settings.safe_summary()["auth"]
    assert settings.safe_summary()["auth"] == "token"


def test_basic_auth_fallback_is_explicit():
    settings = GraylogSettings(
        endpoint="https://graylog.example.test",
        username="api-user",
        password=SecretStr("api-password"),
    )

    headers = settings.auth_headers()
    assert headers["Authorization"].startswith("Basic ")
    assert settings.safe_summary()["auth"] == "basic"


def test_auth_is_required():
    with pytest.raises(ValidationError, match="GRAYLOG_TOKEN or both"):
        GraylogSettings(endpoint="https://graylog.example.test")


def test_endpoint_must_not_be_empty():
    with pytest.raises(ValidationError):
        GraylogSettings(endpoint="", token=SecretStr("token-value"))
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_config.py -q
```

Expected: FAIL because current settings allow `admin/admin` defaults and expose only username/password auth.

- [x] **Step 3: Implement safe settings**

Replace `mcp_graylog/config.py` with:

```python
"""Configuration for the Graylog MCP server."""

import base64
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GraylogSettings(BaseSettings):
    """Graylog connection settings.

    Prefer access tokens for automation. Graylog accepts access tokens via
    HTTP Basic auth where the token is used as both username and password.
    """

    endpoint: str = Field(..., description="Graylog server base URL")
    token: SecretStr | None = Field(None, description="Graylog access token")
    username: str | None = Field(None, description="Legacy Graylog username")
    password: SecretStr | None = Field(None, description="Legacy Graylog password")
    verify_ssl: bool = Field(True, description="Verify TLS certificates")
    timeout: float = Field(30.0, gt=0, description="HTTP timeout in seconds")

    model_config = SettingsConfigDict(
        env_prefix="GRAYLOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("endpoint")
    @classmethod
    def normalize_endpoint(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized:
            raise ValueError("GRAYLOG_ENDPOINT must not be empty")
        return normalized

    @model_validator(mode="after")
    def require_auth(self) -> "GraylogSettings":
        if self.token is not None:
            return self
        if self.username and self.password is not None:
            return self
        raise ValueError("GRAYLOG_TOKEN or both GRAYLOG_USERNAME and GRAYLOG_PASSWORD are required")

    def auth_mode(self) -> Literal["token", "basic"]:
        return "token" if self.token is not None else "basic"

    def auth_headers(self) -> dict[str, str]:
        if self.token is not None:
            secret = self.token.get_secret_value()
            raw_credentials = f"{secret}:{secret}"
        else:
            password = self.password.get_secret_value() if self.password else ""
            raw_credentials = f"{self.username}:{password}"

        encoded = base64.b64encode(raw_credentials.encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {encoded}"}

    def safe_summary(self) -> dict[str, str | float | bool]:
        return {
            "endpoint": self.endpoint,
            "auth": self.auth_mode(),
            "verify_ssl": self.verify_ssl,
            "timeout": self.timeout,
        }


class ServerSettings(BaseSettings):
    """MCP server runtime settings."""

    transport: Literal["stdio", "streamable-http"] = Field("stdio")
    host: str = Field("127.0.0.1")
    port: int = Field(8000, ge=1, le=65535)
    path: str = Field("/mcp")
    log_level: str = Field("INFO")

    model_config = SettingsConfigDict(
        env_prefix="MCP_SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def load_graylog_settings() -> GraylogSettings:
    return GraylogSettings()


def load_server_settings() -> ServerSettings:
    return ServerSettings()
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
./venv/bin/python -m pytest tests/test_config.py -q
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add mcp_graylog/config.py tests/test_config.py
git commit -m "feat: add safe graylog settings"
```

---

### Task 3: Add Typed Models For MCP Inputs And Graylog Requests

**Files:**
- Create: `mcp_graylog/models.py`
- Test: `tests/test_models.py`

- [x] **Step 1: Write failing model tests**

Create `tests/test_models.py`:

```python
import pytest
from pydantic import ValidationError

from mcp_graylog.models import (
    AggregateLogsInput,
    MessageSearchInput,
    RelativeTimeRange,
)


def test_relative_time_range_converts_to_graylog_timerange():
    timerange = RelativeTimeRange(value=90, unit="m")

    assert timerange.to_graylog() == {"type": "relative", "range": 5400}


def test_relative_time_range_rejects_graylog_shaped_extra_fields():
    with pytest.raises(ValidationError):
        RelativeTimeRange.model_validate({"type": "relative", "range": 300})


def test_message_search_input_builds_messages_payload():
    payload = MessageSearchInput(
        query="level:ERROR",
        streams=["stream-1"],
        fields=["timestamp", "message"],
        limit=25,
        offset=10,
    ).to_graylog_payload()

    assert payload == {
        "query": "level:ERROR",
        "timerange": {"type": "relative", "range": 3600},
        "streams": ["stream-1"],
        "fields": ["timestamp", "message"],
        "size": 25,
        "from": 10,
    }


def test_aggregate_logs_input_builds_aggregate_payload():
    payload = AggregateLogsInput(
        query="*",
        field="level",
        metric="count",
        limit=5,
    ).to_graylog_payload()

    assert payload == {
        "query": "*",
        "timerange": {"type": "relative", "range": 3600},
        "group_by": [{"field": "level", "limit": 5}],
        "metrics": [{"function": "count"}],
    }


def test_aggregate_logs_input_builds_field_metric_payload():
    payload = AggregateLogsInput(
        query="source:example.org",
        field="http_method",
        metric="avg",
        metric_field="took_ms",
    ).to_graylog_payload()

    assert payload["query"] == "source:example.org"
    assert payload["group_by"] == [{"field": "http_method", "limit": 10}]
    assert payload["metrics"] == [{"function": "avg", "field": "took_ms"}]


def test_aggregate_logs_input_builds_percentile_metric_payload():
    payload = AggregateLogsInput(
        field="http_method",
        metric="percentile",
        metric_field="took_ms",
        percentile=90,
    ).to_graylog_payload()

    assert payload["metrics"] == [
        {
            "function": "percentile",
            "field": "took_ms",
            "configuration": {"percentile": 90.0},
        }
    ]


def test_limit_validation_is_strict():
    with pytest.raises(ValidationError):
        MessageSearchInput(query="*", limit=0)

    with pytest.raises(ValidationError):
        MessageSearchInput(query="*", limit=1001)


def test_non_count_metric_requires_metric_field():
    with pytest.raises(ValidationError, match="metric_field is required"):
        AggregateLogsInput(field="level", metric="sum")


def test_cardinality_is_not_a_graylog_scripting_metric():
    with pytest.raises(ValidationError):
        AggregateLogsInput(field="level", metric="cardinality")


def test_payload_lists_do_not_mutate_model_lists():
    search = MessageSearchInput(
        query="*",
        streams=["stream-1"],
        fields=["timestamp"],
    )

    payload = search.to_graylog_payload()
    payload["streams"].append("stream-2")
    payload["fields"].append("message")

    assert search.streams == ["stream-1"]
    assert search.fields == ["timestamp"]
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_models.py -q
```

Expected: FAIL because `mcp_graylog.models` does not exist.

- [x] **Step 3: Implement models**

Create `mcp_graylog/models.py`:

```python
"""Typed models for MCP tool inputs and Graylog API payloads."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RelativeTimeRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: int = Field(1, ge=1)
    unit: Literal["s", "m", "h", "d", "w"] = Field("h")

    def to_seconds(self) -> int:
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        return self.value * multipliers[self.unit]

    def to_graylog(self) -> dict[str, int | str]:
        return {"type": "relative", "range": self.to_seconds()}


class AbsoluteTimeRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_: str = Field(..., alias="from")
    to: str

    def to_graylog(self) -> dict[str, str]:
        return {"type": "absolute", "from": self.from_, "to": self.to}


class KeywordTimeRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keyword: str = Field(..., min_length=1)

    def to_graylog(self) -> dict[str, str]:
        return {"type": "keyword", "keyword": self.keyword}


TimeRange = RelativeTimeRange | AbsoluteTimeRange | KeywordTimeRange


class MessageSearchInput(BaseModel):
    query: str = Field("*", min_length=1)
    timerange: TimeRange = Field(default_factory=RelativeTimeRange)
    streams: list[str] = Field(default_factory=list)
    fields: list[str] = Field(
        default_factory=lambda: ["timestamp", "source", "level", "message"]
    )
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be empty")
        return stripped

    def to_graylog_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "query": self.query,
            "timerange": self.timerange.to_graylog(),
            "size": self.limit,
            "from": self.offset,
        }
        if self.streams:
            payload["streams"] = list(self.streams)
        if self.fields:
            payload["fields"] = list(self.fields)
        return payload


class AggregateLogsInput(BaseModel):
    query: str = Field("*", min_length=1)
    timerange: TimeRange = Field(default_factory=RelativeTimeRange)
    streams: list[str] = Field(default_factory=list)
    field: str = Field(..., min_length=1)
    metric: Literal[
        "average",
        "avg",
        "count",
        "latest",
        "max",
        "min",
        "percentile",
        "stdDev",
        "sum",
        "sumOfSquares",
        "variance",
    ] = "count"
    metric_field: str | None = Field(
        None,
        description="Target field for non-count Graylog aggregation metrics.",
    )
    percentile: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Percentile value used when metric is percentile.",
    )
    limit: int = Field(10, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be empty")
        return stripped

    @model_validator(mode="after")
    def validate_metric_configuration(self) -> "AggregateLogsInput":
        if self.metric != "count" and not self.metric_field:
            raise ValueError("metric_field is required for non-count metrics")
        if self.metric == "percentile" and self.percentile is None:
            raise ValueError("percentile is required for percentile metrics")
        if self.metric != "percentile" and self.percentile is not None:
            raise ValueError("percentile is only valid for percentile metrics")
        return self

    def to_graylog_payload(self) -> dict[str, object]:
        metric: dict[str, object] = {"function": self.metric}
        if self.metric_field:
            metric["field"] = self.metric_field
        if self.percentile is not None:
            metric["configuration"] = {"percentile": self.percentile}

        payload: dict[str, object] = {
            "query": self.query,
            "timerange": self.timerange.to_graylog(),
            "group_by": [{"field": self.field, "limit": self.limit}],
            "metrics": [metric],
        }
        if self.streams:
            payload["streams"] = list(self.streams)
        return payload


class StreamSummary(BaseModel):
    id: str
    title: str
    description: str | None = None
    disabled: bool = False


class ToolError(BaseModel):
    error: str
    detail: str | None = None
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
./venv/bin/python -m pytest tests/test_models.py -q
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add mcp_graylog/models.py tests/test_models.py
git commit -m "feat: add typed graylog mcp models"
```

---

### Task 4: Implement Modern Graylog Client

**Files:**
- Create: `mcp_graylog/graylog_client.py`
- Test: `tests/test_graylog_client.py`

- [x] **Step 1: Write failing client tests**

Create `tests/test_graylog_client.py`:

```python
import httpx
import pytest

from mcp_graylog.config import GraylogSettings
from mcp_graylog.graylog_client import GraylogApiError, GraylogClient
from mcp_graylog.models import AggregateLogsInput, MessageSearchInput


def make_client(handler):
    transport = httpx.MockTransport(handler)
    settings = GraylogSettings(endpoint="https://graylog.example.test", token="secret-token")
    return GraylogClient(settings=settings, transport=transport)


def test_search_messages_uses_current_graylog_endpoint():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = request.read().decode()
        return httpx.Response(200, json={"messages": [], "total_results": 0})

    client = make_client(handler)

    result = client.search_messages(MessageSearchInput(query="level:ERROR"))

    assert result["total_results"] == 0
    assert captured["method"] == "POST"
    assert captured["path"] == "/api/search/messages"
    assert '"query":"level:ERROR"' in captured["body"]


def test_aggregate_uses_current_graylog_endpoint():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        return httpx.Response(200, json={"datarows": []})

    client = make_client(handler)

    result = client.aggregate(AggregateLogsInput(query="*", field="level"))

    assert result == {"datarows": []}
    assert captured["method"] == "POST"
    assert captured["path"] == "/api/search/aggregate"


def test_auth_header_is_redacted_in_error_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthorized"})

    client = make_client(handler)

    with pytest.raises(GraylogApiError) as exc_info:
        client.search_messages(MessageSearchInput(query="*"))

    message = str(exc_info.value)
    assert "401" in message
    assert "secret-token" not in message
    assert "Authorization" not in message


def test_stream_id_rejects_encoded_path_separators_before_http_request():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={})

    client = make_client(handler)

    for stream_id in ("abc%2Fdef", "abc%3Fdef", "abc%23def"):
        with pytest.raises(ValueError, match="stream_id"):
            client.get_stream(stream_id)

    assert requests == []


def test_successful_non_json_response_becomes_graylog_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    client = make_client(handler)

    with pytest.raises(GraylogApiError) as exc_info:
        client.get_system_info()

    assert "non-JSON" in str(exc_info.value)
    assert "JSONDecodeError" not in str(exc_info.value)
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_graylog_client.py -q
```

Expected: FAIL because `mcp_graylog.graylog_client` does not exist.

- [x] **Step 3: Implement client**

Create `mcp_graylog/graylog_client.py`:

```python
"""Graylog REST API adapter."""

import logging
from collections.abc import Mapping
from typing import Any

import httpx

from .config import GraylogSettings
from .models import AggregateLogsInput, MessageSearchInput

logger = logging.getLogger(__name__)


class GraylogApiError(RuntimeError):
    """Raised when Graylog returns an error response or cannot be reached."""


class GraylogClient:
    def __init__(
        self,
        settings: GraylogSettings,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._client = httpx.Client(
            base_url=settings.endpoint,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                **settings.auth_headers(),
            },
            verify=settings.verify_ssl,
            timeout=settings.timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, json: Mapping[str, Any] | None = None) -> dict[str, Any]:
        logger.debug("graylog request method=%s path=%s auth=%s", method, path, self.settings.auth_mode())
        try:
            response = self._client.request(method, path, json=json)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = exc.response.text[:500]
            raise GraylogApiError(f"Graylog API returned HTTP {status}: {body}") from exc
        except httpx.HTTPError as exc:
            raise GraylogApiError(f"Graylog API request failed: {exc}") from exc

        if not response.content:
            return {}
        return response.json()

    def search_messages(self, search: MessageSearchInput) -> dict[str, Any]:
        return self._request("POST", "/api/search/messages", json=search.to_graylog_payload())

    def aggregate(self, aggregation: AggregateLogsInput) -> dict[str, Any]:
        return self._request("POST", "/api/search/aggregate", json=aggregation.to_graylog_payload())

    def list_streams(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/streams")
        return response.get("streams", [])

    def get_stream(self, stream_id: str) -> dict[str, Any]:
        clean_stream_id = stream_id.strip()
        if not clean_stream_id:
            raise ValueError("stream_id must not be empty")
        if any(character in clean_stream_id for character in "/?#%\\"):
            raise ValueError("stream_id must not contain path separators or percent-encoding")
        return self._request("GET", f"/api/streams/{clean_stream_id}")

    def get_system_info(self) -> dict[str, Any]:
        return self._request("GET", "/api/system")
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
./venv/bin/python -m pytest tests/test_graylog_client.py -q
./venv/bin/python -m ruff check mcp_graylog/graylog_client.py tests/test_graylog_client.py
./venv/bin/python -m mypy mcp_graylog/graylog_client.py tests/test_graylog_client.py
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add mcp_graylog/graylog_client.py tests/test_graylog_client.py
git commit -m "feat: use current graylog search api"
```

---

### Task 5: Rewrite MCP Server As Typed Tool Layer

**Files:**
- Modify: `mcp_graylog/server.py`
- Test: `tests/test_server_tools.py`

- [x] **Step 1: Write failing server tool tests**

Create `tests/test_server_tools.py`:

```python
from mcp_graylog.models import MessageSearchInput
from mcp_graylog.server import create_tool_handlers


class FakeGraylogClient:
    def __init__(self):
        self.search_input = None

    def search_messages(self, search: MessageSearchInput):
        self.search_input = search
        return {"messages": [{"message": {"message": "hello"}}], "total_results": 1}

    def aggregate(self, aggregation):
        return {"datarows": [{"key": ["ERROR"], "values": [3]}]}

    def list_streams(self):
        return [{"id": "stream-1", "title": "App Logs", "disabled": False}]

    def get_stream(self, stream_id: str):
        return {"id": stream_id, "title": "App Logs", "disabled": False}

    def get_system_info(self):
        return {"version": "6.3.0"}


def test_search_logs_returns_structured_dict_not_json_string():
    fake = FakeGraylogClient()
    handlers = create_tool_handlers(fake)

    result = handlers.search_logs(MessageSearchInput(query="level:ERROR"))

    assert isinstance(result, dict)
    assert result["total_results"] == 1
    assert fake.search_input.query == "level:ERROR"


def test_search_streams_by_name_filters_case_insensitive():
    handlers = create_tool_handlers(FakeGraylogClient())

    result = handlers.search_streams_by_name("app")

    assert result == {
        "search_term": "app",
        "matches": [{"id": "stream-1", "title": "App Logs", "disabled": False}],
        "total_matches": 1,
    }
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_server_tools.py -q
```

Expected: FAIL because current `server.py` has global client side effects and returns JSON strings.

- [x] **Step 3: Implement typed handlers and MCP registration**

Replace `mcp_graylog/server.py` with:

```python
"""MCP tool registration for Graylog."""

from dataclasses import dataclass
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .graylog_client import GraylogClient
from .models import AggregateLogsInput, MessageSearchInput

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass
class ToolHandlers:
    graylog: GraylogClient

    def search_logs(self, search: MessageSearchInput) -> dict[str, Any]:
        return self.graylog.search_messages(search)

    def search_stream_logs(self, stream_id: str, search: MessageSearchInput) -> dict[str, Any]:
        search.streams = [stream_id]
        return self.graylog.search_messages(search)

    def aggregate_logs(self, aggregation: AggregateLogsInput) -> dict[str, Any]:
        return self.graylog.aggregate(aggregation)

    def list_streams(self) -> dict[str, list[dict[str, Any]]]:
        return {"streams": self.graylog.list_streams()}

    def get_stream_info(self, stream_id: str) -> dict[str, Any]:
        return self.graylog.get_stream(stream_id)

    def search_streams_by_name(self, stream_name: str) -> dict[str, Any]:
        search_term = stream_name.strip().lower()
        matches = []
        for stream in self.graylog.list_streams():
            title = str(stream.get("title", ""))
            if search_term in title.lower():
                matches.append(
                    {
                        "id": stream.get("id"),
                        "title": stream.get("title"),
                        "disabled": stream.get("disabled", False),
                    }
                )
        return {"search_term": stream_name, "matches": matches, "total_matches": len(matches)}

    def get_system_info(self) -> dict[str, Any]:
        return self.graylog.get_system_info()

    def get_error_logs(self, hours: int = 1, limit: int = 100) -> dict[str, Any]:
        search = MessageSearchInput(query="level:ERROR OR level:CRITICAL OR level:FATAL", limit=limit)
        search.timerange.value = hours
        search.timerange.unit = "h"
        return self.graylog.search_messages(search)

    def get_log_count_by_level(self, hours: int = 1) -> dict[str, Any]:
        aggregation = AggregateLogsInput(query="*", field="level")
        aggregation.timerange.value = hours
        aggregation.timerange.unit = "h"
        return self.graylog.aggregate(aggregation)


def create_tool_handlers(graylog: GraylogClient) -> ToolHandlers:
    return ToolHandlers(graylog=graylog)


def create_mcp_server(graylog: GraylogClient, log_level: LogLevel = "INFO") -> FastMCP:
    mcp = FastMCP("graylog", log_level=log_level)
    handlers = create_tool_handlers(graylog)

    mcp.tool()(handlers.search_logs)
    mcp.tool()(handlers.search_stream_logs)
    mcp.tool()(handlers.aggregate_logs)
    mcp.tool()(handlers.list_streams)
    mcp.tool()(handlers.get_stream_info)
    mcp.tool()(handlers.search_streams_by_name)
    mcp.tool()(handlers.get_system_info)
    mcp.tool()(handlers.get_error_logs)
    mcp.tool()(handlers.get_log_count_by_level)

    return mcp
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
./venv/bin/python -m pytest tests/test_server_tools.py -q
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add mcp_graylog/server.py tests/test_server_tools.py
git commit -m "feat: make mcp tools typed and side effect free"
```

---

### Task 6: Add Codex-First CLI Transport Selection

**Files:**
- Create: `mcp_graylog/cli.py`
- Test: `tests/test_cli.py`

- [x] **Step 1: Write failing CLI tests**

Create `tests/test_cli.py`:

```python
from mcp_graylog.cli import parse_args


def test_default_transport_is_stdio_for_codex():
    args = parse_args([])

    assert args.transport == "stdio"


def test_http_transport_is_explicit():
    args = parse_args(["--transport", "streamable-http", "--host", "127.0.0.1", "--port", "9001", "--path", "/mcp"])

    assert args.transport == "streamable-http"
    assert args.host == "127.0.0.1"
    assert args.port == 9001
    assert args.path == "/mcp"
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_cli.py -q
```

Expected: FAIL because `mcp_graylog.cli` does not exist.

- [x] **Step 3: Implement CLI**

Create `mcp_graylog/cli.py`:

```python
"""Command line entrypoint for mcp-graylog."""

import argparse
from collections.abc import Sequence
from typing import Literal

from .config import load_graylog_settings
from .graylog_client import GraylogClient
from .server import LogLevel, create_mcp_server

Transport = Literal["stdio", "streamable-http"]
LOG_LEVELS: tuple[LogLevel, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Graylog MCP server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--path", default="/mcp")
    parser.add_argument("--log-level", choices=LOG_LEVELS, default="INFO")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    transport: Transport = args.transport
    log_level: LogLevel = args.log_level

    graylog_settings = load_graylog_settings()
    with GraylogClient(settings=graylog_settings) as graylog:
        mcp = create_mcp_server(graylog, log_level=log_level)

        if transport == "streamable-http":
            mcp.settings.host = args.host
            mcp.settings.port = args.port
            mcp.settings.streamable_http_path = args.path

        mcp.run(transport=transport)
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
./venv/bin/python -m pytest tests/test_cli.py -q
./venv/bin/python -m ruff check mcp_graylog/cli.py tests/test_cli.py
./venv/bin/python -m mypy mcp_graylog/cli.py tests/test_cli.py
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add mcp_graylog/cli.py tests/test_cli.py
git commit -m "feat: add codex first mcp cli"
```

---

### Task 7: Update Docker And Entrypoint For Explicit HTTP MCP

**Files:**
- Modify: `Dockerfile`
- Modify: `entrypoint.sh`
- Modify: `docker-compose.yml`
- Test: `tests/test_container_files.py`

- [x] **Step 1: Write failing container config tests**

Create `tests/test_container_files.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_healthcheck_targets_mcp_port():
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "mcp-graylog" in dockerfile
    assert "streamable-http" in dockerfile
    assert "socket.create_connection(('127.0.0.1', 8000)" in dockerfile
    assert "/health_check" not in dockerfile
    assert "requests" not in dockerfile


def test_entrypoint_requires_graylog_endpoint_and_auth():
    entrypoint = (ROOT / "entrypoint.sh").read_text()

    assert "GRAYLOG_ENDPOINT is required" in entrypoint
    assert "GRAYLOG_TOKEN or GRAYLOG_USERNAME/GRAYLOG_PASSWORD is required" in entrypoint
    assert 'exec "$@"' in entrypoint
    assert "python -m mcp_graylog.server" not in entrypoint
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_container_files.py -q
```

Expected: FAIL because the current container files expose `/health_check` and run `python -m mcp_graylog.server`.

- [x] **Step 3: Update Dockerfile**

Replace `Dockerfile` with:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mcp_graylog/ ./mcp_graylog/
COPY entrypoint.sh ./entrypoint.sh

RUN pip install --no-cache-dir . \
    && chmod +x ./entrypoint.sh \
    && useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 8000), timeout=5).close()" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["mcp-graylog", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000", "--path", "/mcp"]
```

- [x] **Step 4: Update entrypoint and compose**

Replace `entrypoint.sh` with:

```bash
#!/bin/sh
set -eu

if [ -z "${GRAYLOG_ENDPOINT:-}" ]; then
  echo "GRAYLOG_ENDPOINT is required" >&2
  exit 1
fi

if [ -z "${GRAYLOG_TOKEN:-}" ]; then
  if [ -z "${GRAYLOG_USERNAME:-}" ] || [ -z "${GRAYLOG_PASSWORD:-}" ]; then
    echo "GRAYLOG_TOKEN or GRAYLOG_USERNAME/GRAYLOG_PASSWORD is required" >&2
    exit 1
  fi
fi

exec "$@"
```

Replace `docker-compose.yml` with:

```yaml
services:
  mcp-graylog:
    build: .
    container_name: mcp-graylog-server
    ports:
      - "8000:8000"
    environment:
      GRAYLOG_ENDPOINT: ${GRAYLOG_ENDPOINT}
      GRAYLOG_TOKEN: ${GRAYLOG_TOKEN}
      GRAYLOG_USERNAME: ${GRAYLOG_USERNAME:-}
      GRAYLOG_PASSWORD: ${GRAYLOG_PASSWORD:-}
      GRAYLOG_VERIFY_SSL: ${GRAYLOG_VERIFY_SSL:-true}
      GRAYLOG_TIMEOUT: ${GRAYLOG_TIMEOUT:-30}
    restart: unless-stopped
```

- [x] **Step 5: Run test to verify it passes**

Run:

```bash
./venv/bin/python -m pytest tests/test_container_files.py -q
```

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add Dockerfile entrypoint.sh docker-compose.yml tests/test_container_files.py
git commit -m "feat: make docker run explicit http mcp"
```

---

### Task 8: Audit And Refresh Repository Documentation

**Files:**
- Modify: `README.md`
- Modify: `DOCUMENTATION.md`
- Modify: `env.example`
- Modify: `examples/basic_usage.py`
- Modify: `example_setup.sh`
- Modify: `test_cursor_integration.py`
- Test: `tests/test_docs.py`

- [x] **Step 1: Write failing docs tests**

Create `tests/test_docs.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_documents_codex_stdio_first():
    readme = (ROOT / "README.md").read_text()

    assert "[mcp_servers.graylog]" in readme
    assert 'command = "uv"' in readme
    assert 'args = ["run", "mcp-graylog"]' in readme
    assert "GRAYLOG_TOKEN" in readme
    assert "/api/search/messages" in readme
    assert "/api/search/aggregate" in readme
    assert "/health_check" not in readme
    assert "python -m mcp_graylog.server" not in readme


def test_long_form_documentation_uses_current_api_and_transport():
    documentation = (ROOT / "DOCUMENTATION.md").read_text()

    assert "Codex stdio" in documentation
    assert "Streamable HTTP" in documentation
    assert "/api/search/messages" in documentation
    assert "/api/search/aggregate" in documentation
    assert "/api/search/universal" not in documentation
    assert "/health_check" not in documentation


def test_env_example_uses_token_auth():
    env_example = (ROOT / "env.example").read_text()

    assert "GRAYLOG_TOKEN=" in env_example
    assert "GRAYLOG_PASSWORD=" not in env_example
    assert "MCP_SERVER_TRANSPORT=stdio" in env_example


def test_examples_do_not_teach_legacy_password_or_healthcheck_setup():
    checked_paths = [
        ROOT / "examples" / "basic_usage.py",
        ROOT / "example_setup.sh",
        ROOT / "test_cursor_integration.py",
    ]
    combined = "\n".join(path.read_text() for path in checked_paths)

    assert "GRAYLOG_TOKEN" in combined
    assert "GRAYLOG_PASSWORD" not in combined
    assert "/health_check" not in combined
    assert "python -m mcp_graylog.server" not in combined
    assert "/api/search/universal" not in combined
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_docs.py -q
```

Expected: FAIL because current docs lead with Docker and username/password, and `DOCUMENTATION.md` still documents `/api/search/universal/*` and `/health_check`.

- [x] **Step 3: Replace README opening sections**

Replace the README sections from title through configuration with:

````markdown
# MCP Graylog Server

Model Context Protocol server for querying Graylog logs from Codex and other MCP clients.

## Primary Use Case: Codex

Codex should run this server over stdio. Add this to `~/.codex/config.toml`:

```toml
[mcp_servers.graylog]
command = "uv"
args = ["run", "mcp-graylog"]

[mcp_servers.graylog.env]
GRAYLOG_ENDPOINT = "https://graylog.example.com"
GRAYLOG_TOKEN = "your-graylog-access-token"
GRAYLOG_VERIFY_SSL = "true"
GRAYLOG_TIMEOUT = "30"
```

Graylog access tokens are used with Basic auth as `token:token`.

## Remote HTTP Mode

Use Streamable HTTP only when the server is shared or deployed remotely:

```bash
mcp-graylog --transport streamable-http --host 127.0.0.1 --port 8000 --path /mcp
```

Docker runs this HTTP mode intentionally and exposes `/mcp`.

## Graylog API

The server targets the Graylog 6+ Search Scripting API:

- `POST /api/search/messages` for log messages.
- `POST /api/search/aggregate` for aggregations.
- `GET /api/streams` and `GET /api/streams/{stream_id}` for stream metadata.
- `GET /api/system` for connectivity and system information.

## Tools

- `search_logs`: search messages by query, timerange, streams, fields, limit, and offset.
- `search_stream_logs`: search messages in one stream.
- `aggregate_logs`: aggregate logs by a field with `count`, `avg`, `average`, `latest`, `max`, `min`, `percentile`, `stdDev`, `sum`, `sumOfSquares`, `variance`.
- `list_streams`: list Graylog streams.
- `get_stream_info`: read one stream.
- `search_streams_by_name`: find streams by title.
- `get_system_info`: read Graylog system metadata.
- `get_error_logs`: shortcut for ERROR/CRITICAL/FATAL messages.
- `get_log_count_by_level`: shortcut aggregation by `level`.
````

Keep the later examples only if they use the new typed input shape and do not mention `/health_check`.

- [x] **Step 4: Replace long-form documentation with current reference**

Replace `DOCUMENTATION.md` with:

````markdown
# MCP Graylog Server Documentation

## Runtime Model

The primary runtime for this project is Codex stdio. Codex starts the server as a local subprocess and communicates over MCP stdio. In stdio mode the process must not write diagnostic text to stdout; logs belong on stderr.

Streamable HTTP is supported only as an explicit remote/shared deployment mode. The HTTP endpoint is `/mcp`.

## Codex Configuration

```toml
[mcp_servers.graylog]
command = "uv"
args = ["run", "mcp-graylog"]

[mcp_servers.graylog.env]
GRAYLOG_ENDPOINT = "https://graylog.example.com"
GRAYLOG_TOKEN = "your-graylog-access-token"
GRAYLOG_VERIFY_SSL = "true"
GRAYLOG_TIMEOUT = "30"
```

## Authentication

Use Graylog access tokens for automation. The server sends the token using Basic auth with the token as both username and password. Username/password configuration is retained only as a legacy fallback for local migrations.

## Graylog API Endpoints

- `POST /api/search/messages`: message search.
- `POST /api/search/aggregate`: grouped metrics and counts.
- `GET /api/streams`: stream listing.
- `GET /api/streams/{stream_id}`: stream detail.
- `GET /api/system`: connectivity and version metadata.

## Tool Inputs

Message searches accept `query`, `timerange`, `streams`, `fields`, `limit`, and `offset`. Aggregations accept `query`, `timerange`, `streams`, `field`, `metric`, and `limit`.

## Transport Selection

Run stdio locally:

```bash
mcp-graylog
```

Run Streamable HTTP explicitly:

```bash
mcp-graylog --transport streamable-http --host 127.0.0.1 --port 8000 --path /mcp
```
````

- [x] **Step 5: Update env example**

Replace `env.example` with:

```text
# Graylog Configuration
GRAYLOG_ENDPOINT=https://your-graylog-server
GRAYLOG_TOKEN=your-graylog-access-token

# Optional Graylog Settings
GRAYLOG_VERIFY_SSL=true
GRAYLOG_TIMEOUT=30

# Optional HTTP MCP Settings
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
MCP_SERVER_PATH=/mcp
MCP_SERVER_TRANSPORT=stdio
```

- [x] **Step 6: Update repository examples and setup helpers**

Replace the example output in `examples/basic_usage.py` so it demonstrates the new input models:

```python
"""Usage examples for the Graylog MCP server."""


def print_codex_config() -> None:
    print(
        """
[mcp_servers.graylog]
command = "uv"
args = ["run", "mcp-graylog"]

[mcp_servers.graylog.env]
GRAYLOG_ENDPOINT = "https://graylog.example.com"
GRAYLOG_TOKEN = "your-graylog-access-token"
GRAYLOG_VERIFY_SSL = "true"
GRAYLOG_TIMEOUT = "30"
""".strip()
    )


def print_search_example() -> None:
    print(
        {
            "query": "level:ERROR",
            "timerange": {"value": 1, "unit": "h"},
            "streams": ["stream-id"],
            "fields": ["timestamp", "source", "level", "message"],
            "limit": 50,
            "offset": 0,
        }
    )


def print_aggregation_example() -> None:
    print(
        {
            "query": "*",
            "timerange": {"value": 24, "unit": "h"},
            "field": "level",
            "metric": "count",
            "limit": 10,
        }
    )


if __name__ == "__main__":
    print_codex_config()
    print_search_example()
    print_aggregation_example()
```

Replace `example_setup.sh` with:

```bash
#!/bin/sh
set -eu

export GRAYLOG_ENDPOINT="${GRAYLOG_ENDPOINT:-https://graylog.example.com}"
export GRAYLOG_TOKEN="${GRAYLOG_TOKEN:-replace-with-graylog-access-token}"
export GRAYLOG_VERIFY_SSL="${GRAYLOG_VERIFY_SSL:-true}"
export GRAYLOG_TIMEOUT="${GRAYLOG_TIMEOUT:-30}"
export MCP_SERVER_TRANSPORT="${MCP_SERVER_TRANSPORT:-stdio}"

echo "Codex stdio configuration:"
echo "[mcp_servers.graylog]"
echo "command = \"uv\""
echo "args = [\"run\", \"mcp-graylog\"]"
echo
echo "[mcp_servers.graylog.env]"
echo "GRAYLOG_ENDPOINT = \"$GRAYLOG_ENDPOINT\""
echo "GRAYLOG_TOKEN = \"<redacted>\""
```

Replace the stale Docker/password config generation in `test_cursor_integration.py` with a current config-only smoke script:

```python
"""Generate current MCP Graylog client configuration examples."""

import os


def codex_stdio_config() -> str:
    endpoint = os.getenv("GRAYLOG_ENDPOINT", "https://graylog.example.com")
    return f"""
[mcp_servers.graylog]
command = "uv"
args = ["run", "mcp-graylog"]

[mcp_servers.graylog.env]
GRAYLOG_ENDPOINT = "{endpoint}"
GRAYLOG_TOKEN = "<redacted>"
GRAYLOG_VERIFY_SSL = "true"
GRAYLOG_TIMEOUT = "30"
""".strip()


def streamable_http_config() -> str:
    return """
[mcp_servers.graylog]
url = "http://127.0.0.1:8000/mcp"
""".strip()


if __name__ == "__main__":
    print(codex_stdio_config())
    print()
    print(streamable_http_config())
```

- [x] **Step 7: Run test to verify it passes**

Run:

```bash
./venv/bin/python -m pytest tests/test_docs.py -q
```

Expected: PASS.

- [x] **Step 8: Commit**

```bash
git add README.md DOCUMENTATION.md env.example examples/basic_usage.py example_setup.sh test_cursor_integration.py tests/test_docs.py
git commit -m "docs: refresh repository documentation for current mcp graylog"
```

---

### Task 9: Remove Legacy Entrypoints And Compatibility Debt

**Files:**
- Delete: `run_server.py`
- Modify: `start.sh`
- Modify: `mcp_graylog/__init__.py`
- Optional delete after imports are gone: `mcp_graylog/client.py`
- Test: `tests/test_legacy_cleanup.py`

- [x] **Step 1: Write failing cleanup tests**

Create `tests/test_legacy_cleanup.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run_server_py_removed():
    assert not (ROOT / "run_server.py").exists()


def test_start_sh_does_not_write_stdio_noise_before_mcp_start():
    start_sh = (ROOT / "start.sh").read_text()

    assert "python -m mcp_graylog.server" not in start_sh
    assert "exec mcp-graylog" in start_sh


def test_init_exports_version_only():
    init_py = (ROOT / "mcp_graylog" / "__init__.py").read_text()

    assert "__version__" in init_py
    assert "GraylogClient" not in init_py
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_legacy_cleanup.py -q
```

Expected: FAIL because legacy entrypoints still exist.

- [x] **Step 3: Delete invalid runner and simplify start script**

Delete `run_server.py`.

Replace `start.sh` with:

```bash
#!/bin/sh
set -eu

if [ -x "./venv/bin/mcp-graylog" ]; then
  exec ./venv/bin/mcp-graylog "$@"
fi

exec mcp-graylog "$@"
```

Replace `mcp_graylog/__init__.py` with:

```python
"""Graylog MCP server package."""

__version__ = "0.2.0"
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
./venv/bin/python -m pytest tests/test_legacy_cleanup.py -q
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add start.sh mcp_graylog/__init__.py tests/test_legacy_cleanup.py
git rm run_server.py
git commit -m "chore: remove legacy graylog server entrypoints"
```

---

### Task 10: Final Verification And Migration Notes

**Files:**
- Modify: `Makefile`
- Test: full suite and import smoke.

- [x] **Step 1: Update Makefile commands**

Replace test/lint targets in `Makefile` with:

```makefile
.PHONY: test lint typecheck

test:
	./venv/bin/python -m pytest -q

lint:
	./venv/bin/python -m ruff check .

typecheck:
	./venv/bin/python -m mypy mcp_graylog
```

- [x] **Step 2: Run full tests**

Run:

```bash
./venv/bin/python -m pytest -q
```

Expected: PASS for all tests.

- [x] **Step 3: Run lint**

Run:

```bash
./venv/bin/python -m ruff check .
```

Expected: PASS.

- [x] **Step 4: Run import smoke**

Run:

```bash
GRAYLOG_ENDPOINT=https://graylog.example.test GRAYLOG_TOKEN=test-token ./venv/bin/python -c "from mcp_graylog.cli import parse_args; assert parse_args([]).transport == 'stdio'"
```

Expected: command exits with code 0.

- [x] **Step 5: Commit**

```bash
git add Makefile
git commit -m "chore: add final refactor verification commands"
```

---

## Self-Review

- Spec coverage: plan covers Codex transport (`stdio` first), optional Streamable HTTP, official MCP SDK migration, Graylog current search endpoints, token auth, log redaction, packaging, Docker, full repository documentation refresh, and test reproducibility.
- Placeholder scan: no `TBD`, `TODO`, "implement later", or unstated edge handling remains in task steps.
- Type consistency: `MessageSearchInput`, `AggregateLogsInput`, `GraylogSettings`, `GraylogClient`, `create_mcp_server`, and `parse_args` are introduced before later tasks reference them.

## Execution Status

Status: implemented on branch `codex/mth-1-graylog-refactor`.

Completed scope:

- Modernized package metadata and dependency declarations for Python 3.11+.
- Replaced legacy settings with token-first, redacted, typed configuration.
- Added typed Graylog 6+ request/response models.
- Replaced legacy Graylog universal search usage with current search messages and aggregate APIs.
- Reworked MCP server tools to use typed inputs and side-effect-free handlers.
- Added Codex-first CLI with stdio as the default transport and explicit Streamable HTTP opt-in.
- Updated Docker, compose, entrypoint, examples, and docs for the current runtime.
- Removed obsolete runner scripts, legacy helper modules, and stale tests.
- Added MCP client configuration examples for Codex, Claude Code, Cursor, OpenCode, Hermes, and OpenClaw.
- Added beginner dependency installation instructions.

Verification completed before merge:

```bash
./venv/bin/python -m pytest -q
./venv/bin/python -m ruff check .
./venv/bin/python -m mypy mcp_graylog
git diff --check
GRAYLOG_ENDPOINT=https://graylog.example.test GRAYLOG_TOKEN=test-token ./venv/bin/python -c "from mcp_graylog.cli import parse_args; assert parse_args([]).transport == 'stdio'"
docker build -t mcp-graylog:merge-check .
```

Merge plan: squash branch into `main` as one refactoring commit.
