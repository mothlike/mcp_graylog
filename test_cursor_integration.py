#!/usr/bin/env python3
"""
Test script for Cursor MCP Graylog integration.

This script tests the Docker setup and provides configuration examples
for integrating the MCP Graylog server with Cursor.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def check_environment_variables():
    """Check if required environment variables are set."""
    print("Checking environment variables...")

    required_vars = {
        "GRAYLOG_ENDPOINT": "Graylog server URL (e.g., https://graylog.example.com:9000)",
        "GRAYLOG_USERNAME": "Graylog username for authentication",
        "GRAYLOG_PASSWORD": "Graylog password for authentication",
    }

    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"Environment variable {var}: {'*' * len(value)} ({description})")
        else:
            missing_vars.append(var)
            print(f"Missing: {var} ({description})")

    if missing_vars:
        print(f"\nWarning: {len(missing_vars)} environment variables are missing.")
        print("You can set them in your environment or create a .env file.")
        return False

    print("Using Username/Password authentication")
    return True


def check_docker_image():
    """Check if the Docker image exists."""
    print("\nChecking Docker image...")

    try:
        result = subprocess.run(
            [
                "docker",
                "images",
                "mcp-graylog:latest",
                "--format",
                "{{.Repository}}:{{.Tag}}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout.strip():
            print("Docker image mcp-graylog:latest found")
            return True
        else:
            print("Docker image mcp-graylog:latest not found")
            print("You can build it with: docker build -t mcp-graylog .")
            return False

    except subprocess.CalledProcessError:
        print("ERROR: Failed to check Docker images")
        return False
    except FileNotFoundError:
        print("ERROR: Docker not found. Please install Docker.")
        return False


def test_container_startup():
    """Test if the container can start successfully."""
    print("\nTesting container startup...")

    # Get environment variables for the test
    env_vars = {
        "GRAYLOG_ENDPOINT": os.getenv("GRAYLOG_ENDPOINT", "https://example.com:9000"),
        "GRAYLOG_USERNAME": os.getenv("GRAYLOG_USERNAME", "test"),
        "GRAYLOG_PASSWORD": os.getenv("GRAYLOG_PASSWORD", "test"),
        "GRAYLOG_VERIFY_SSL": "false",
        "GRAYLOG_TIMEOUT": "10",
    }

    try:
        # Build the docker run command
        cmd = [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            "mcp-graylog-test",
            "-p",
            "8001:8000",  # Use different port for testing
        ]

        # Add environment variables
        for key, value in env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])

        cmd.append("mcp-graylog:latest")

        print(f"Running: {' '.join(cmd)}")

        # Start the container
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            container_id = result.stdout.strip()
            print(f"Container started with ID: {container_id}")

            # Wait a moment for startup
            import time

            time.sleep(3)

            # Check if container is still running
            check_result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"id={container_id}",
                    "--format",
                    "{{.Status}}",
                ],
                capture_output=True,
                text=True,
            )

            if check_result.stdout.strip():
                print("Container starts successfully")

                # Stop the test container
                subprocess.run(["docker", "stop", container_id], capture_output=True)
                print("Container started (timeout reached - this is expected)")
                return True
            else:
                print("Container stopped unexpectedly")
                return False
        else:
            print(f"ERROR: Failed to start container: {result.stderr}")
            return False

    except Exception as e:
        print(f"ERROR: Container test failed: {e}")
        return False


def generate_cursor_config():
    """Generate Cursor configuration examples."""
    print("\nGenerating Cursor configuration examples...")

    # Get current environment variables
    endpoint = os.getenv("GRAYLOG_ENDPOINT", "https://your-graylog-server:9000")
    username = os.getenv("GRAYLOG_USERNAME", "your-username")
    password = os.getenv("GRAYLOG_PASSWORD", "your-password")

    print("Using Username/Password configuration")

    # Generate Docker-based configuration
    docker_config = {
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

    print("Copy this configuration to Cursor settings:")
    print(json.dumps(docker_config, indent=2))

    return True


def main():
    """Main test function."""
    print("Testing Cursor MCP Graylog Integration")
    print("=" * 60)

    # Run tests
    env_ok = check_environment_variables()
    docker_ok = check_docker_image()
    container_ok = test_container_startup()
    config_ok = generate_cursor_config()

    # Summary
    print("\nTest Summary:")
    print(f"Environment Variables: {'PASS' if env_ok else 'FAIL'}")
    print(f"Docker Image: {'PASS' if docker_ok else 'FAIL'}")
    print(f"Container Test: {'PASS' if container_ok else 'FAIL'}")
    print(f"Configuration: {'PASS' if config_ok else 'FAIL'}")

    all_passed = all([env_ok, docker_ok, container_ok, config_ok])

    if all_passed:
        print("\nAll tests passed! Your setup is ready for Cursor integration.")
        return 0
    else:
        print("\nSome tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
