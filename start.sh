#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        log "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    log "Activating virtual environment..."
    source venv/bin/activate
}

# Function to install dependencies
install_dependencies() {
    log "Installing dependencies..."
    pip install -r requirements.txt
}

# Function to validate environment
validate_environment() {
    log "Validating environment..."
    
    # Check if required environment variables are set
    if [ -z "$GRAYLOG_ENDPOINT" ]; then
        log "WARNING: GRAYLOG_ENDPOINT not set, using default"
        export GRAYLOG_ENDPOINT=${GRAYLOG_ENDPOINT:-https://graylog-server:9000}
    fi
    
    if [ -z "$GRAYLOG_USERNAME" ]; then
        log "WARNING: GRAYLOG_USERNAME not set, using default"
        export GRAYLOG_USERNAME=${GRAYLOG_USERNAME:-admin}
    fi
    
    if [ -z "$GRAYLOG_PASSWORD" ]; then
        log "WARNING: GRAYLOG_PASSWORD not set, using default"
        export GRAYLOG_PASSWORD=${GRAYLOG_PASSWORD:-admin}
    fi
    
    # Set default values for other environment variables
    export GRAYLOG_VERIFY_SSL=${GRAYLOG_VERIFY_SSL:-true}
    export GRAYLOG_TIMEOUT=${GRAYLOG_TIMEOUT:-30}
    export MCP_SERVER_PORT=${MCP_SERVER_PORT:-8000}
    export MCP_SERVER_HOST=${MCP_SERVER_HOST:-0.0.0.0}
    export LOG_LEVEL=${LOG_LEVEL:-INFO}
}

# Function to start the application
start_application() {
    log "Starting MCP Graylog server..."
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Start the server
    python -m mcp_graylog.server
}

# Main execution
main() {
    log "Starting MCP Graylog server (development mode)..."
    
    # Check and setup virtual environment
    check_venv
    
    # Install dependencies
    install_dependencies
    
    # Validate environment
    validate_environment
    
    # Start the application
    start_application
}

# Run main function
main "$@" 