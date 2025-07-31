#!/usr/bin/env python3
"""
MCP Graylog Server Runner

This script provides a simple way to run the MCP Graylog server.
It handles environment setup and provides helpful error messages.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["GRAYLOG_ENDPOINT", "GRAYLOG_USERNAME", "GRAYLOG_PASSWORD"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("Starting MCP Graylog Server")
        print("Warning: Make sure to set authentication credentials:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nYou can set these in your environment or create a .env file.")
        return False

    return True


def main():
    """Main entry point."""
    setup_logging()

    # Check environment
    env_ok = check_environment()

    try:
        from mcp_graylog.server import app

        print("Server imported successfully")
        print("Server ready to start")

        # Start the server
        app.run()

    except ImportError as e:
        print(f"ERROR: Failed to import server module: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return 1

    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
