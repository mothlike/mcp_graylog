#!/usr/bin/env python3
"""Simple script to run the MCP Graylog server."""

import os
import sys
import uvicorn

# Set environment variables (credentials should be set externally)
os.environ['GRAYLOG_ENDPOINT'] = os.environ.get('GRAYLOG_ENDPOINT', 'https://your-graylog-server:9000)
os.environ['MCP_SERVER_HOST'] = os.environ.get('MCP_SERVER_HOST', '0.0.0.0')
os.environ['MCP_SERVER_PORT'] = os.environ.get('MCP_SERVER_PORT', '8001')
os.environ['LOG_LEVEL'] = os.environ.get('LOG_LEVEL', 'INFO')

def main():
    """Run the MCP Graylog server."""
    print("🚀 Starting MCP Graylog Server")
    print("=" * 40)
    print(f"Endpoint: {os.environ['GRAYLOG_ENDPOINT']}")
    print(f"Server: {os.environ['MCP_SERVER_HOST']}:{os.environ['MCP_SERVER_PORT']}")
    print()
    print("⚠️  Make sure to set authentication credentials:")
    print("   GRAYLOG_USERNAME and GRAYLOG_PASSWORD (for Basic auth)")
    print()
    
    try:
        # Import the server module
        from mcp_graylog.server import app, config
        
        print("✅ Server imported successfully")
        print("📊 Server ready to start")
        
        print()
        print("🌐 Starting server...")
        print(f"   URL: http://localhost:{config.server.port}")
        print("   Press Ctrl+C to stop")
        print()
        
        # Run the server
        uvicorn.run(
            app,
            host=config.server.host,
            port=config.server.port,
            log_level=config.server.log_level.lower()
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 