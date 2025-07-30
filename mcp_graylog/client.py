"""Graylog API client for MCP server."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, Field

from .config import config

logger = logging.getLogger(__name__)


class TimeRange(BaseModel):
    """Time range for log queries."""
    
    type: str = Field(..., description="Time range type (relative, absolute)")
    from_: Optional[str] = Field(None, alias="from", description="Start time")
    to: Optional[str] = Field(None, description="End time")


class QueryParams(BaseModel):
    """Query parameters for log search."""
    
    query: str = Field(..., description="Search query")
    time_range: Optional[str] = Field(None, description="Time range (e.g., '1h', '24h', '7d')")
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    limit: int = Field(50, description="Maximum number of results")
    offset: int = Field(0, description="Result offset")
    sort: Optional[str] = Field(None, description="Sort field")
    sort_direction: str = Field("desc", description="Sort direction")
    stream_id: Optional[str] = Field(None, description="Stream ID to search in")
    decorate: Optional[bool] = Field(None, description="Whether to decorate messages (default: true)")
    filter: Optional[str] = Field(None, description="Additional filter query")
    highlight: Optional[bool] = Field(None, description="Enable/disable result highlighting")


class AggregationParams(BaseModel):
    """Aggregation parameters for log analysis."""
    
    type: str = Field(..., description="Aggregation type (terms, date_histogram, etc.)")
    field: str = Field(..., description="Field to aggregate on")
    size: int = Field(10, description="Number of buckets")
    interval: Optional[str] = Field(None, description="Time interval for date histograms")


class GraylogClient:
    """Client for interacting with Graylog API."""
    
    def __init__(self):
        self.base_url = config.graylog.endpoint.rstrip('/')
        self.session = requests.Session()
        
        # Set up authentication headers
        auth_headers = config.auth_headers
        logger.debug(f"Setting up authentication headers: {list(auth_headers.keys())}")
        
        self.session.headers.update(auth_headers)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        self.session.verify = config.graylog.verify_ssl
        self.timeout = config.graylog.timeout
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Graylog API."""
        url = urljoin(self.base_url, endpoint)
        
        try:
            logger.debug(f"Making {method} request to {url}")
            logger.debug(f"Headers: {dict(self.session.headers)}")
            if data:
                logger.debug(f"Request data: {data}")
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Handle authentication errors specifically
            if response.status_code == 401:
                logger.error("Authentication failed - check your username and password")
                logger.error(f"Response text: {response.text}")
                raise requests.exceptions.HTTPError(
                    f"Authentication failed (401): {response.text}"
                )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Graylog API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            raise
    
    def _parse_time_range(self, time_range: str) -> Dict[str, Any]:
        """Parse time range string into Graylog format for /relative endpoint."""
        if not time_range:
            return {}
        # Supported units and their conversion to seconds
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
        unit = time_range[-1]
        value = time_range[:-1]
        if unit in units and value.isdigit():
            seconds = int(value) * units[unit]
            return {"range": seconds}
        # If not a recognized relative range, fallback to previous logic (absolute)
        return {"range": time_range}
    
    def search_logs(self, params: QueryParams) -> Dict[str, Any]:
        """Search logs using Graylog API."""
        search_params = {
            "query": params.query,
            "limit": params.limit,
            "offset": params.offset,
        }
        
        # Add sort parameter if specified
        if params.sort:
            search_params["sort"] = f"{params.sort}:{params.sort_direction}"
        
        # Add time range - default to 1h if not specified
        time_range = params.time_range or "1h"
        search_params.update(self._parse_time_range(time_range))
        
        # Add fields filter
        if params.fields:
            search_params["fields"] = ",".join(params.fields)
        
        # Add stream filter - ensure it's passed as a list
        if params.stream_id:
            search_params["streams"] = [params.stream_id]
        
        # Add advanced Graylog parameters if set
        if params.decorate is not None:
            search_params["decorate"] = params.decorate
        if params.filter is not None:
            search_params["filter"] = params.filter
        if params.highlight is not None:
            search_params["highlight"] = params.highlight
        
        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        
        logger.debug(f"Search params: {search_params}")
        
        # Use GET and query parameters for this endpoint
        return self._make_request("GET", "/api/search/universal/relative", params=search_params)
    
    def get_log_statistics(
        self, 
        query: str, 
        time_range: str,
        aggregation: AggregationParams
    ) -> Dict[str, Any]:
        """Get log statistics and aggregations."""
        search_params = {
            "query": query,
            "range": self._parse_time_range(time_range).get("range", {}),
            "interval": aggregation.interval,
            "field": aggregation.field,
            "size": aggregation.size
        }
        
        endpoint = f"/api/search/universal/relative/{aggregation.type}"
        return self._make_request("POST", endpoint, data=search_params)
    
    def list_streams(self) -> List[Dict[str, Any]]:
        """List all available streams."""
        response = self._make_request("GET", "/api/streams")
        return response.get("streams", [])
    
    def get_stream_info(self, stream_id: str) -> Dict[str, Any]:
        """Get detailed information about a stream."""
        return self._make_request("GET", f"/api/streams/{stream_id}")
    
    def search_stream_logs(self, stream_id: str, params: QueryParams) -> Dict[str, Any]:
        """
        Search logs within a specific stream.
        
        Args:
            stream_id: The ID of the stream to search in
            params: Query parameters including query, time range, fields, and limit
            
        Returns:
            Dictionary containing search results with messages and metadata
        """
        # Ensure stream_id is set in params
        params.stream_id = stream_id
        
        # Validate query - if empty or None, use wildcard
        if not params.query or params.query.strip() == "":
            params.query = "*"
        
        # Ensure limit is within reasonable bounds
        if params.limit < 1:
            params.limit = 1
        elif params.limit > 100:
            params.limit = 100
        
        logger.debug(f"Searching stream {stream_id} with query: {params.query}")
        return self.search_logs(params)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get Graylog system information."""
        return self._make_request("GET", "/api/system")
    
    def test_connection(self) -> bool:
        """Test connection to Graylog server."""
        try:
            # First test basic connectivity
            response = self.session.get(
                self.base_url,
                timeout=self.timeout
            )
            logger.debug(f"Basic connectivity test: {response.status_code}")
            
            # Then test API authentication
            self.get_system_info()
            logger.info("✅ Graylog connection successful")
            return True
        except requests.exceptions.HTTPError as e:
            if "401" in str(e):
                logger.error("❌ Authentication failed - check your username and password")
                logger.error(f"   Authorization header: {self.session.headers.get('Authorization', 'None')[:20]}...")
            else:
                logger.error(f"❌ HTTP error during connection test: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            # Handle connection errors more gracefully for mock endpoints
            if "mock-graylog-server" in self.base_url or "graylog-server" in self.base_url:
                logger.debug(f"Mock Graylog server not available: {e}")
                return False
            else:
                logger.error(f"❌ Connection test failed: {e}")
                return False
        except Exception as e:
            # Handle other errors more gracefully for mock endpoints
            if "mock-graylog-server" in self.base_url or "graylog-server" in self.base_url:
                logger.debug(f"Mock Graylog server not available: {e}")
                return False
            else:
                logger.error(f"❌ Connection test failed: {e}")
                return False 