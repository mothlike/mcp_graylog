"""Tests for Graylog client."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from mcp_graylog.client import GraylogClient, QueryParams, AggregationParams
from mcp_graylog.config import config


class TestGraylogClient:
    """Test cases for GraylogClient."""

    @pytest.fixture
    def client(self):
        """Create a GraylogClient instance for testing."""
        with patch("mcp_graylog.client.config") as mock_config:
            mock_config.graylog.endpoint = "https://test-graylog:9000"
            mock_config.graylog.verify_ssl = True
            mock_config.graylog.timeout = 30
            mock_config.auth_headers = {"Authorization": "Bearer test-token"}
            return GraylogClient()

    def test_init(self, client):
        """Test client initialization."""
        assert client.base_url == "https://test-graylog:9000"
        assert client.timeout == 30

    def test_parse_time_range_hours(self, client):
        """Test parsing time range with hours."""
        result = client._parse_time_range("2h")
        assert "range" in result
        assert "from" in result["range"]
        assert "to" in result["range"]

    def test_parse_time_range_days(self, client):
        """Test parsing time range with days."""
        result = client._parse_time_range("3d")
        assert "range" in result
        assert "from" in result["range"]
        assert "to" in result["range"]

    def test_parse_time_range_weeks(self, client):
        """Test parsing time range with weeks."""
        result = client._parse_time_range("1w")
        assert "range" in result
        assert "from" in result["range"]
        assert "to" in result["range"]

    def test_parse_time_range_empty(self, client):
        """Test parsing empty time range."""
        result = client._parse_time_range("")
        assert result == {}

    def test_parse_time_range_none(self, client):
        """Test parsing None time range."""
        result = client._parse_time_range(None)
        assert result == {}

    @patch("requests.Session.request")
    def test_make_request_success(self, mock_request, client):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = client._make_request("GET", "/api/test")

        assert result == {"test": "data"}
        mock_request.assert_called_once()

    @patch("requests.Session.request")
    def test_make_request_failure(self, mock_request, client):
        """Test failed API request."""
        mock_request.side_effect = Exception("Connection failed")

        with pytest.raises(Exception):
            client._make_request("GET", "/api/test")

    @patch.object(GraylogClient, "_make_request")
    def test_search_logs(self, mock_make_request, client):
        """Test search logs functionality."""
        mock_make_request.return_value = {"messages": [], "total_results": 0}

        params = QueryParams(query="test query", time_range="1h", limit=10)

        result = client.search_logs(params)

        assert result == {"messages": [], "total_results": 0}
        mock_make_request.assert_called_once()

    @patch.object(GraylogClient, "_make_request")
    def test_search_logs_default_time_range(self, mock_make_request, client):
        """Test search logs with default time range (1h) when time_range is None."""
        mock_make_request.return_value = {"messages": [], "total_results": 0}

        params = QueryParams(
            query="test query",
            time_range=None,  # Explicitly set to None to test default
            limit=10,
        )

        result = client.search_logs(params)

        assert result == {"messages": [], "total_results": 0}
        mock_make_request.assert_called_once()

        # Verify that the time range was set to "1h" in the request
        call_args = mock_make_request.call_args
        request_params = call_args[1]["params"]  # Get the params argument
        assert "range" in request_params  # Should have range parameter

    @patch.object(GraylogClient, "_make_request")
    def test_get_log_statistics(self, mock_make_request, client):
        """Test get log statistics functionality."""
        mock_make_request.return_value = {"buckets": []}

        aggregation = AggregationParams(type="terms", field="level", size=10)

        result = client.get_log_statistics("test query", "24h", aggregation)

        assert result == {"buckets": []}
        mock_make_request.assert_called_once()

    @patch.object(GraylogClient, "_make_request")
    def test_list_streams(self, mock_make_request, client):
        """Test list streams functionality."""
        mock_make_request.return_value = {
            "streams": [{"id": "1", "title": "Test Stream"}]
        }

        result = client.list_streams()

        assert result == [{"id": "1", "title": "Test Stream"}]
        mock_make_request.assert_called_once_with("GET", "/api/streams")

    @patch.object(GraylogClient, "_make_request")
    def test_get_stream_info(self, mock_make_request, client):
        """Test get stream info functionality."""
        mock_make_request.return_value = {"id": "1", "title": "Test Stream"}

        result = client.get_stream_info("1")

        assert result == {"id": "1", "title": "Test Stream"}
        mock_make_request.assert_called_once_with("GET", "/api/streams/1")

    @patch.object(GraylogClient, "_make_request")
    def test_get_system_info(self, mock_make_request, client):
        """Test get system info functionality."""
        mock_make_request.return_value = {"version": "4.0.0"}

        result = client.get_system_info()

        assert result == {"version": "4.0.0"}
        mock_make_request.assert_called_once_with("GET", "/api/system")

    @patch.object(GraylogClient, "get_system_info")
    def test_test_connection_success(self, mock_get_system_info, client):
        """Test successful connection test."""
        mock_get_system_info.return_value = {"version": "4.0.0"}

        result = client.test_connection()

        assert result is True

    @patch.object(GraylogClient, "get_system_info")
    def test_test_connection_failure(self, mock_get_system_info, client):
        """Test failed connection test."""
        mock_get_system_info.side_effect = Exception("Connection failed")

        result = client.test_connection()

        assert result is False


class TestQueryParams:
    """Test cases for QueryParams."""

    def test_query_params_creation(self):
        """Test QueryParams creation."""
        params = QueryParams(query="test query", time_range="1h", limit=50)

        assert params.query == "test query"
        assert params.time_range == "1h"
        assert params.limit == 50
        assert params.offset == 0
        assert params.sort_direction == "desc"

    def test_query_params_defaults(self):
        """Test QueryParams default values."""
        params = QueryParams(query="test")

        assert params.limit == 50
        assert params.offset == 0
        assert params.sort_direction == "desc"
        assert params.time_range is None


class TestAggregationParams:
    """Test cases for AggregationParams."""

    def test_aggregation_params_creation(self):
        """Test AggregationParams creation."""
        params = AggregationParams(type="terms", field="level", size=20)

        assert params.type == "terms"
        assert params.field == "level"
        assert params.size == 20
        assert params.interval is None

    def test_aggregation_params_with_interval(self):
        """Test AggregationParams with interval."""
        params = AggregationParams(
            type="date_histogram", field="timestamp", size=10, interval="1h"
        )

        assert params.type == "date_histogram"
        assert params.field == "timestamp"
        assert params.interval == "1h"
