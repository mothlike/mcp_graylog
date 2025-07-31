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
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Install the package in development mode
    pip install -e .
}

# Function to test the installation
test_installation() {
    log "Testing installation..."
    
    # Test if we can import the config
    if python -c "from mcp_graylog.config import config; print('Config import successful')" 2>/dev/null; then
        log "Installation successful!"
        return 0
    else
        log "Installation failed. Please check the error messages above."
        return 1
    fi
}

# Main execution
main() {
    log "Installing MCP Graylog dependencies..."
    
    # Check and setup virtual environment
    check_venv
    
    # Install dependencies
    install_dependencies
    
    # Test the installation
    test_installation
    
    log "Installation complete! You can now run the server with:"
    log "  ./start.sh"
    log "  or"
    log "  python -m mcp_graylog.server"
}

# Run main function
main "$@" 