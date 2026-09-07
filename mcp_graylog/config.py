"""Configuration for the Graylog MCP server."""

import base64
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GraylogSettings(BaseSettings):
    """Graylog connection settings."""

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
        parsed = urlsplit(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("GRAYLOG_ENDPOINT must be an absolute http(s) URL")
        if parsed.username or parsed.password:
            raise ValueError("GRAYLOG_ENDPOINT must not contain credentials")
        return normalized

    @model_validator(mode="after")
    def require_auth(self) -> "GraylogSettings":
        if self._token_value():
            return self
        if self._basic_credentials():
            return self
        raise ValueError(
            "GRAYLOG_TOKEN or both GRAYLOG_USERNAME and GRAYLOG_PASSWORD are required"
        )

    def auth_mode(self) -> Literal["token", "basic"]:
        return "token" if self._token_value() else "basic"

    def auth_headers(self) -> dict[str, str]:
        if secret := self._token_value():
            raw_credentials = f"{secret}:{secret}"
        else:
            username, password = self._basic_credentials() or ("", "")
            raw_credentials = f"{username}:{password}"

        encoded = base64.b64encode(raw_credentials.encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {encoded}"}

    def safe_summary(self) -> dict[str, str | bool | float]:
        return {
            "endpoint": self.endpoint,
            "auth": self.auth_mode(),
            "verify_ssl": self.verify_ssl,
            "timeout": self.timeout,
        }

    def _token_value(self) -> str | None:
        if self.token is None:
            return None
        token = self.token.get_secret_value().strip()
        return token or None

    def _basic_credentials(self) -> tuple[str, str] | None:
        username = self.username.strip() if self.username else ""
        password = self.password.get_secret_value().strip() if self.password else ""
        if username and password:
            return username, password
        return None


class ServerSettings(BaseSettings):
    """MCP server runtime settings."""

    transport: Literal["stdio", "streamable-http"] = Field("stdio")
    host: str = Field("127.0.0.1")
    port: int = Field(8000, ge=1, le=65535)
    path: str = Field("/mcp")
    log_level: str = Field("INFO")
    dns_rebinding_protection: bool = Field(True)
    allowed_hosts: str = Field("127.0.0.1:*,localhost:*,[::1]:*")
    allowed_origins: str = Field(
        "http://127.0.0.1:*,http://localhost:*,http://[::1]:*"
    )

    model_config = SettingsConfigDict(
        env_prefix="MCP_SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def allowed_host_values(self) -> list[str]:
        return self._split_csv(self.allowed_hosts)

    def allowed_origin_values(self) -> list[str]:
        return self._split_csv(self.allowed_origins)

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]


def load_graylog_settings() -> GraylogSettings:
    return GraylogSettings()  # type: ignore[call-arg]


def load_server_settings() -> ServerSettings:
    return ServerSettings()  # type: ignore[call-arg]
