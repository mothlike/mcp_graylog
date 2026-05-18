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
    timerange: TimeRange = Field(
        default_factory=lambda: RelativeTimeRange.model_validate({})
    )
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
    timerange: TimeRange = Field(
        default_factory=lambda: RelativeTimeRange.model_validate({})
    )
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
