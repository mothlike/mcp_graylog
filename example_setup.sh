#!/bin/bash
# Example setup script for MCP Graylog Server
# Copy this file and modify with your actual credentials

echo "Setting up environment variables for MCP Graylog Server..."

# Graylog server configuration
export GRAYLOG_ENDPOINT="https://your-graylog-server.com"

# Authentication
export GRAYLOG_USERNAME="your_username"
export GRAYLOG_PASSWORD="your_password"

# Server configuration
export MCP_SERVER_HOST="0.0.0.0"
export MCP_SERVER_PORT="8001"
export LOG_LEVEL="INFO"

echo "Environment variables set:"
echo "  GRAYLOG_ENDPOINT: $GRAYLOG_ENDPOINT"
echo "  GRAYLOG_USERNAME: $GRAYLOG_USERNAME"
echo "  MCP_SERVER_PORT: $MCP_SERVER_PORT"

echo ""
echo "To start the server, run:"
echo "  python run_server.py" 