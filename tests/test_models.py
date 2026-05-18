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
