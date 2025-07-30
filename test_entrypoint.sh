#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to test entrypoint script
test_entrypoint() {
    log "Testing entrypoint script..."
    
    # Check if entrypoint script exists
    if [ ! -f "entrypoint.sh" ]; then
        log "ERROR: entrypoint.sh not found"
        exit 1
    fi
    
    # Check if entrypoint script is executable
    if [ ! -x "entrypoint.sh" ]; then
        log "ERROR: entrypoint.sh is not executable"
        exit 1
    fi
    
    log "✓ entrypoint.sh exists and is executable"
}

# Function to test start script
test_start_script() {
    log "Testing start script..."
    
    # Check if start script exists
    if [ ! -f "start.sh" ]; then
        log "ERROR: start.sh not found"
        exit 1
    fi
    
    # Check if start script is executable
    if [ ! -x "start.sh" ]; then
        log "ERROR: start.sh is not executable"
        exit 1
    fi
    
    log "✓ start.sh exists and is executable"
}

# Function to test Dockerfile
test_dockerfile() {
    log "Testing Dockerfile..."
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        log "ERROR: Dockerfile not found"
        exit 1
    fi
    
    # Check if Dockerfile references entrypoint
    if ! grep -q "ENTRYPOINT" Dockerfile; then
        log "ERROR: Dockerfile does not contain ENTRYPOINT directive"
        exit 1
    fi
    
    # Check if Dockerfile copies entrypoint script
    if ! grep -q "COPY entrypoint.sh" Dockerfile; then
        log "ERROR: Dockerfile does not copy entrypoint.sh"
        exit 1
    fi
    
    log "✓ Dockerfile properly configured"
}

# Function to test docker-compose
test_docker_compose() {
    log "Testing docker-compose.yml..."
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        log "ERROR: docker-compose.yml not found"
        exit 1
    fi
    
    # Check if docker-compose.yml has proper configuration
    if ! grep -q "mcp-graylog:" docker-compose.yml; then
        log "ERROR: docker-compose.yml does not contain mcp-graylog service"
        exit 1
    fi
    
    log "✓ docker-compose.yml properly configured"
}

# Main execution
main() {
    log "Running entrypoint tests..."
    
    test_entrypoint
    test_start_script
    test_dockerfile
    test_docker_compose
    
    log "✓ All tests passed!"
    log "The project is properly configured with default entrypoint."
}

# Run main function
main "$@" 