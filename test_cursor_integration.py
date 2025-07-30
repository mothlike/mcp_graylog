#!/usr/bin/env python3
"""Test script for Cursor MCP Graylog integration."""

import os
import sys
import json
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_environment_variables():
    """Test if required environment variables are set."""
    print("=== Environment Variables Test ===")

    required_vars = {
        "GRAYLOG_ENDPOINT": "Graylog server endpoint",
        "GRAYLOG_USERNAME": "Graylog username",
        "GRAYLOG_PASSWORD": "Graylog password",
    }

    missing_vars = []

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} ({description})")
        else:
            missing_vars.append(var)
            print(f"❌ {var}: Not set ({description})")

    print()

    if not missing_vars:
        print("✅ Using Username/Password authentication")
    else:
        print("❌ Missing required authentication variables")

    if missing_vars:
        print(f"\n❌ Missing required variables: {', '.join(missing_vars)}")
        return False

    return True


def test_docker_image():
    """Test if Docker image exists."""
    print("\n=== Docker Image Test ===")

    try:
        result = subprocess.run(
            ["docker", "images", "mcp-graylog:latest"], capture_output=True, text=True
        )

        if result.returncode == 0 and "mcp-graylog" in result.stdout:
            print("✅ Docker image mcp-graylog:latest found")
            return True
        else:
            print("❌ Docker image mcp-graylog:latest not found")
            print("   Run: docker build -t mcp-graylog:latest .")
            return False
    except FileNotFoundError:
        print("❌ Docker not found or not in PATH")
        return False


def test_container_run():
    """Test if container can run with current environment."""
    print("\n=== Container Test ===")

    # Get environment variables
    env_vars = []
    for var in ["GRAYLOG_ENDPOINT", "GRAYLOG_USERNAME", "GRAYLOG_PASSWORD"]:
        value = os.getenv(var)
        if value:
            env_vars.extend(["-e", f"{var}={value}"])

    if not env_vars:
        print("❌ No environment variables set for container test")
        return False

    # Use a unique container name
    import uuid

    container_name = f"test-mcp-graylog-{uuid.uuid4().hex[:8]}"

    try:
        # Clean up any existing test container
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

        # Test container startup (timeout after 10 seconds)
        cmd = (
            ["docker", "run", "--rm", "--name", container_name]
            + env_vars
            + [
                "mcp-graylog:latest",
                "timeout",
                "10",
                "python",
                "-m",
                "mcp_graylog.server",
            ]
        )

        print(f"Testing container with command: {' '.join(cmd[:6])}...")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        if result.returncode == 0 or "Starting MCP Graylog server" in result.stdout:
            print("✅ Container starts successfully")
            return True
        else:
            print("❌ Container failed to start")
            print(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("✅ Container started (timeout reached - this is expected)")
        return True
    except Exception as e:
        print(f"❌ Container test failed: {e}")
        return False
    finally:
        # Clean up
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)


def generate_cursor_config():
    """Generate Cursor configuration based on environment variables."""
    print("\n=== Cursor Configuration ===")

    endpoint = os.getenv("GRAYLOG_ENDPOINT")
    username = os.getenv("GRAYLOG_USERNAME")
    password = os.getenv("GRAYLOG_PASSWORD")

    if not endpoint:
        print("❌ GRAYLOG_ENDPOINT not set")
        return

    if not username or not password:
        print("❌ GRAYLOG_USERNAME and GRAYLOG_PASSWORD must be set")
        return

    print("✅ Using Username/Password configuration")
    config = {
        "mcpServers": {
            "graylog": {
                "command": "docker",
                "args": [
                    "run",
                    "--rm",
                    "-i",
                    "-e",
                    f"GRAYLOG_ENDPOINT={endpoint}",
                    "-e",
                    f"GRAYLOG_USERNAME={username}",
                    "-e",
                    f"GRAYLOG_PASSWORD={password}",
                    "-e",
                    "GRAYLOG_VERIFY_SSL=true",
                    "-e",
                    "GRAYLOG_TIMEOUT=30",
                    "mcp-graylog:latest",
                ],
                "env": {},
            }
        }
    }

    print("\n📋 Copy this configuration to Cursor settings:")
    print(json.dumps(config, indent=2))


def main():
    """Run all tests."""
    print("🔍 Testing Cursor MCP Graylog Integration")
    print("=" * 50)

    # Test environment variables
    env_ok = test_environment_variables()

    # Test Docker image
    docker_ok = test_docker_image()

    # Test container
    container_ok = test_container_run()

    # Generate configuration
    generate_cursor_config()

    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"Docker Image: {'✅' if docker_ok else '❌'}")
    print(f"Container Test: {'✅' if container_ok else '❌'}")

    if env_ok and docker_ok and container_ok:
        print("\n🎉 All tests passed! Your Cursor integration should work.")
        print("Remember to restart Cursor after adding the configuration.")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")


if __name__ == "__main__":
    main()
