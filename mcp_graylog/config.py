"""Configuration management for MCP Graylog server."""

import os
import logging
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class GraylogConfig(BaseSettings):
    """Graylog connection configuration."""

    endpoint: str = Field(
        "http://localhost:9000", description="Graylog server endpoint URL"
    )
    username: str = Field("admin", description="Graylog username")
    password: str = Field("admin", description="Graylog password")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    timeout: int = Field(30, description="Request timeout in seconds")

    model_config = ConfigDict(env_prefix="GRAYLOG_", case_sensitive=False)


class ServerConfig(BaseSettings):
    """MCP server configuration."""

    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field("json", description="Log format")

    model_config = ConfigDict(env_prefix="MCP_SERVER_", case_sensitive=False)


class Config:
    """Main configuration class."""

    def __init__(self):
        self.graylog = GraylogConfig()
        self.server = ServerConfig()

        # Log configuration for debugging
        logger.info(f"Graylog endpoint: {self.graylog.endpoint}")
        logger.info(f"Has username: {bool(self.graylog.username)}")
        logger.info(f"Has password: {bool(self.graylog.password)}")

        # Validate authentication only if not using defaults
        if (
            self.graylog.username == "admin"
            and self.graylog.password == "admin"
            and self.graylog.endpoint == "http://localhost:9000"
        ):
            logger.warning(
                "Using default configuration - set environment variables for production"
            )

    @property
    def auth_headers(self) -> dict:
        """Get authentication headers for Graylog API."""
        import base64

        credentials = f"{self.graylog.username}:{self.graylog.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        logger.info("Using Basic authentication")
        return {"Authorization": f"Basic {encoded}"}


# Global configuration instance
config = Config()
