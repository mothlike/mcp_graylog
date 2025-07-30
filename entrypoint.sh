#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to wait for dependencies
wait_for_dependencies() {
    log "Checking dependencies..."
    
    # Check if required environment variables are set
    if [ -z "$GRAYLOG_ENDPOINT" ]; then
        log "WARNING: GRAYLOG_ENDPOINT not set, using default"
    fi
    
    if [ -z "$GRAYLOG_USERNAME" ]; then
        log "WARNING: GRAYLOG_USERNAME not set, using default"
    fi
    
    if [ -z "$GRAYLOG_PASSWORD" ]; then
        log "WARNING: GRAYLOG_PASSWORD not set, using default"
    fi
}

# Function to validate configuration
validate_config() {
    log "Validating configuration..."
    
    # Check if the application directory exists
    if [ ! -d "/app/mcp_graylog" ]; then
        log "ERROR: Application directory not found"
        exit 1
    fi
    
    # Check if the server module exists
    if [ ! -f "/app/mcp_graylog/server.py" ]; then
        log "ERROR: Server module not found"
        exit 1
    fi
    
    # Check if required Python packages are installed
    log "Checking Python dependencies..."
    if ! python -c "import pydantic_settings" 2>/dev/null; then
        log "ERROR: pydantic-settings package not found. Please ensure all dependencies are installed."
        log "Try running: pip install -r requirements.txt"
        exit 1
    fi
    
    if ! python -c "import pydantic" 2>/dev/null; then
        log "ERROR: pydantic package not found. Please ensure all dependencies are installed."
        log "Try running: pip install -r requirements.txt"
        exit 1
    fi
    
    if ! python -c "import fastmcp" 2>/dev/null; then
        log "ERROR: fastmcp package not found. Please ensure all dependencies are installed."
        log "Try running: pip install -r requirements.txt"
        exit 1
    fi
}

# Function to run database migrations or setup (if needed)
setup_application() {
    log "Setting up application..."
    
    # Create logs directory if it doesn't exist
    mkdir -p /app/logs
    
    # Set proper permissions
    chown -R app:app /app/logs
}

# Function to start the application
start_application() {
    log "Starting MCP Graylog server..."
    
    # Change to app directory
    cd /app
    
    # Start the server
    exec python -m mcp_graylog.server
}

# Main execution
main() {
    log "Starting MCP Graylog container..."
    
    # Wait for dependencies
    wait_for_dependencies
    
    # Validate configuration
    validate_config
    
    # Setup application
    setup_application
    
    # Start the application
    start_application
}

# Run main function
main "$@" 