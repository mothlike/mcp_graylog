import base64

import pytest
from pydantic import SecretStr, ValidationError

from mcp_graylog.config import GraylogSettings


@pytest.fixture(autouse=True)
def clear_graylog_env(monkeypatch):
    for name in (
        "GRAYLOG_ENDPOINT",
        "GRAYLOG_TOKEN",
        "GRAYLOG_USERNAME",
        "GRAYLOG_PASSWORD",
        "GRAYLOG_VERIFY_SSL",
        "GRAYLOG_TIMEOUT",
    ):
        monkeypatch.delenv(name, raising=False)


def _decode_basic_auth(headers: dict[str, str]) -> str:
    scheme, encoded = headers["Authorization"].split(" ", 1)

    assert scheme == "Basic"
    return base64.b64decode(encoded).decode("utf-8")


def test_token_auth_headers_are_basic_and_safe_summary_masks_secret():
    settings = GraylogSettings(
        endpoint=" https://graylog.example.test/ ",
        token=SecretStr("token-value"),
        _env_file=None,
    )

    assert _decode_basic_auth(settings.auth_headers()) == "token-value:token-value"
    assert settings.safe_summary()["auth"] == "token"
    assert "token-value" not in repr(settings.safe_summary())


def test_basic_auth_fallback_is_explicit_and_safe_summary_reports_basic():
    settings = GraylogSettings(
        endpoint="https://graylog.example.test",
        username="api-user",
        password=SecretStr("api-password"),
        _env_file=None,
    )

    assert _decode_basic_auth(settings.auth_headers()) == "api-user:api-password"
    assert settings.safe_summary()["auth"] == "basic"


def test_blank_token_falls_back_to_valid_basic_auth():
    settings = GraylogSettings(
        endpoint="https://graylog.example.test",
        token=SecretStr(" "),
        username="api-user",
        password=SecretStr("api-password"),
        _env_file=None,
    )

    assert settings.auth_mode() == "basic"
    assert _decode_basic_auth(settings.auth_headers()) == "api-user:api-password"


def test_auth_is_required():
    with pytest.raises(ValidationError, match="GRAYLOG_TOKEN or both"):
        GraylogSettings(endpoint="https://graylog.example.test", _env_file=None)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"token": SecretStr("")},
        {"token": SecretStr("   ")},
        {"username": "api-user", "password": SecretStr("")},
        {"username": "api-user", "password": SecretStr("   ")},
        {"username": "   ", "password": SecretStr("api-password")},
    ],
)
def test_auth_rejects_blank_values(kwargs):
    with pytest.raises(ValidationError, match="GRAYLOG_TOKEN or both"):
        GraylogSettings(
            endpoint="https://graylog.example.test",
            _env_file=None,
            **kwargs,
        )


def test_endpoint_must_not_be_empty():
    with pytest.raises(ValidationError):
        GraylogSettings(endpoint="", token=SecretStr("token-value"), _env_file=None)


def test_endpoint_must_not_contain_credentials():
    for endpoint in (
        "https://user:secret@graylog.example.test",
        "user:secret@graylog.example.test",
    ):
        with pytest.raises(ValidationError):
            GraylogSettings(
                endpoint=endpoint,
                token=SecretStr("token-value"),
                _env_file=None,
            )


def test_endpoint_must_be_absolute_http_url():
    for endpoint in ("graylog.example.test", "ftp://graylog.example.test"):
        with pytest.raises(ValidationError, match="absolute http"):
            GraylogSettings(
                endpoint=endpoint,
                token=SecretStr("token-value"),
                _env_file=None,
            )
