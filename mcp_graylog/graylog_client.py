"""Graylog 6+ Search Scripting API client."""

import json as jsonlib
import logging
from collections.abc import Mapping
from typing import Any

import httpx

from .config import GraylogSettings
from .models import AggregateLogsInput, MessageSearchInput

logger = logging.getLogger(__name__)

_SENSITIVE_RESPONSE_KEYS = {
    "authorization",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
}


class GraylogApiError(RuntimeError):
    """Raised when Graylog returns an error response or cannot be reached."""


class GraylogClient:
    """Synchronous adapter for Graylog 6+ Search Scripting API endpoints."""

    def __init__(
        self,
        settings: GraylogSettings,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._secret_values = self._collect_secret_values(settings)
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

    def __enter__(self) -> "GraylogClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def search_messages(self, search: MessageSearchInput) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/search/messages",
            json=search.to_graylog_payload(),
        )

    def aggregate(self, aggregation: AggregateLogsInput) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/search/aggregate",
            json=aggregation.to_graylog_payload(),
        )

    def list_streams(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/streams")
        streams = response.get("streams")
        if isinstance(streams, list):
            return streams
        return []

    def get_stream(self, stream_id: str) -> dict[str, Any]:
        clean_stream_id = stream_id.strip()
        if not clean_stream_id:
            raise ValueError("stream_id must not be empty")
        if any(character in clean_stream_id for character in "/?#%\\"):
            raise ValueError(
                "stream_id must not contain path separators or percent-encoding"
            )
        return self._request("GET", f"/api/streams/{clean_stream_id}")

    def get_system_info(self) -> dict[str, Any]:
        return self._request("GET", "/api/system")

    def _request(
        self,
        method: str,
        path: str,
        json: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.debug(
            "graylog request method=%s path=%s auth=%s",
            method,
            path,
            self.settings.auth_mode(),
        )
        try:
            response = self._client.request(method, path, json=json)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = self._safe_response_body(exc.response)
            message = f"Graylog API returned HTTP {status}: {body}"
            raise GraylogApiError(self._redact(message)) from exc
        except httpx.HTTPError as exc:
            message = f"Graylog API request failed: {exc}"
            raise GraylogApiError(self._redact(message)) from exc

        if not response.content:
            return {}

        try:
            parsed = response.json()
        except jsonlib.JSONDecodeError as exc:
            body = self._redact(response.text[:500])
            raise GraylogApiError(
                f"Graylog API returned a non-JSON response: {body}"
            ) from exc

        if not isinstance(parsed, dict):
            raise GraylogApiError("Graylog API returned a JSON value, not an object")
        return parsed

    def _safe_response_body(self, response: httpx.Response) -> str:
        try:
            parsed = response.json()
        except jsonlib.JSONDecodeError:
            return self._redact(response.text[:500])

        sanitized = self._sanitize_json_value(parsed)
        return self._redact(jsonlib.dumps(sanitized, ensure_ascii=False)[:500])

    def _sanitize_json_value(self, value: object) -> object:
        if isinstance(value, Mapping):
            sanitized: dict[str, object] = {}
            for key, item in value.items():
                key_text = str(key)
                if key_text.lower() in _SENSITIVE_RESPONSE_KEYS:
                    continue
                sanitized[key_text] = self._sanitize_json_value(item)
            return sanitized
        if isinstance(value, list):
            return [self._sanitize_json_value(item) for item in value]
        if isinstance(value, str):
            return self._redact(value)
        return value

    def _redact(self, value: str) -> str:
        redacted = value.replace("Authorization", "[redacted-header]")
        redacted = redacted.replace("authorization", "[redacted-header]")
        for secret in self._secret_values:
            redacted = redacted.replace(secret, "[redacted]")
        return redacted

    @staticmethod
    def _collect_secret_values(settings: GraylogSettings) -> set[str]:
        secrets = {settings.auth_headers()["Authorization"]}
        if settings.token is not None:
            token = settings.token.get_secret_value().strip()
            if token:
                secrets.add(token)
        if settings.password is not None:
            password = settings.password.get_secret_value().strip()
            if password:
                secrets.add(password)
        return secrets
