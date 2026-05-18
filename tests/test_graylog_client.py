import json
from collections.abc import Callable

import httpx
import pytest

from mcp_graylog.config import GraylogSettings
from mcp_graylog.graylog_client import GraylogApiError, GraylogClient
from mcp_graylog.models import AggregateLogsInput, MessageSearchInput


def make_settings() -> GraylogSettings:
    return GraylogSettings.model_validate(
        {
            "endpoint": "https://graylog.example.test",
            "token": "secret-token",
        }
    )


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> GraylogClient:
    return GraylogClient(
        settings=make_settings(),
        transport=httpx.MockTransport(handler),
    )


def make_search(query: str) -> MessageSearchInput:
    return MessageSearchInput.model_validate({"query": query})


def make_aggregation(query: str, field: str) -> AggregateLogsInput:
    return AggregateLogsInput.model_validate({"query": query, "field": field})


def test_search_messages_uses_current_graylog_endpoint_and_query_payload() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = request.read().decode()
        return httpx.Response(200, json={"messages": [], "total_results": 0})

    client = make_client(handler)

    result = client.search_messages(make_search("level:ERROR"))

    assert result["total_results"] == 0
    assert captured["method"] == "POST"
    assert captured["path"] == "/api/search/messages"
    body = json.loads(captured["body"])
    assert body["query"] == "level:ERROR"
    assert "query_string" not in body


def test_aggregate_uses_current_graylog_endpoint() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        return httpx.Response(200, json={"datarows": []})

    client = make_client(handler)

    result = client.aggregate(make_aggregation("*", "level"))

    assert result == {"datarows": []}
    assert captured["method"] == "POST"
    assert captured["path"] == "/api/search/aggregate"


def test_auth_secret_values_are_redacted_in_error_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "message": "Unauthorized",
                "Authorization": request.headers["Authorization"],
                "token": "secret-token",
            },
        )

    client = make_client(handler)

    with pytest.raises(GraylogApiError) as exc_info:
        client.search_messages(make_search("*"))

    message = str(exc_info.value)
    assert "401" in message
    assert "secret-token" not in message
    assert "Authorization" not in message
    assert make_settings().auth_headers()["Authorization"] not in message


def test_list_streams_handles_missing_streams_as_empty_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/streams"
        return httpx.Response(200, json={"total": 0})

    client = make_client(handler)

    assert client.list_streams() == []


def test_blank_stream_id_rejects_before_http_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={})

    client = make_client(handler)

    with pytest.raises(ValueError, match="stream_id"):
        client.get_stream("  ")

    assert requests == []


def test_stream_id_rejects_path_injection_characters_before_http_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={})

    client = make_client(handler)

    for stream_id in ("abc/def", "abc?def", "abc#def", "abc\\def"):
        with pytest.raises(ValueError, match="stream_id"):
            client.get_stream(stream_id)

    assert requests == []


def test_stream_id_rejects_encoded_path_separators_before_http_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={})

    client = make_client(handler)

    for stream_id in ("abc%2Fdef", "abc%3Fdef", "abc%23def"):
        with pytest.raises(ValueError, match="stream_id"):
            client.get_stream(stream_id)

    assert requests == []


def test_http_transport_errors_become_graylog_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("network unavailable", request=request)

    client = make_client(handler)

    with pytest.raises(GraylogApiError, match="request failed"):
        client.get_system_info()


def test_successful_non_json_response_becomes_graylog_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    client = make_client(handler)

    with pytest.raises(GraylogApiError) as exc_info:
        client.get_system_info()

    assert "non-JSON" in str(exc_info.value)
    assert "JSONDecodeError" not in str(exc_info.value)
