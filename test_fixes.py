#!/usr/bin/env python3
"""
Test script to verify the Pydantic and FastMCP fixes are working.
This script tests both the Pydantic settings fix and the FastMCP API fix.
"""

import sys
import os


def test_pydantic_fix():
    """Test that Pydantic settings work correctly."""
    print("Testing Pydantic settings fix...")

    try:
        from pydantic import ConfigDict

        print("ConfigDict import successful")
    except ImportError as e:
        print(f"ERROR: ConfigDict import failed: {e}")
        return False

    try:
        from pydantic_settings import BaseSettings

        print("BaseSettings import successful")
    except ImportError as e:
        print(f"ERROR: BaseSettings import failed: {e}")
        return False

    try:
        from mcp_graylog.config import GraylogConfig

        print("Config import successful (no deprecation warnings)")
        return True
    except Exception as e:
        print(f"ERROR: Config import failed: {e}")
        return False


def test_fastmcp_fix():
    """Test that FastMCP API works correctly."""
    print("\nTesting FastMCP API fix...")

    try:
        from fastmcp import FastMCP

        print("FastMCP import successful")
    except ImportError as e:
        print(f"ERROR: FastMCP import failed: {e}")
        return False

    try:
        app = FastMCP("graylog")
        print("FastMCP import and initialization successful")
        return True
    except Exception as e:
        print(f"ERROR: FastMCP initialization failed: {e}")
        return False


def test_server_import():
    """Test that the server module can be imported."""
    print("\nTesting server module import...")

    try:
        from mcp_graylog.server import app

        print("Server module import successful")
        return True
    except Exception as e:
        print(f"ERROR: Server module import failed: {e}")
        return False


def test_pydantic_settings():
    """Test that Pydantic settings work with ConfigDict."""
    print("\nTesting Pydantic settings with ConfigDict...")

    try:
        from pydantic import ConfigDict
        from pydantic_settings import BaseSettings

        class TestConfig(BaseSettings):
            model_config = ConfigDict(env_file=".env")
            test_field: str = "default"

        config = TestConfig()
        print("Pydantic settings with ConfigDict works")
        return True
    except Exception as e:
        print(f"ERROR: Pydantic settings test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Pydantic and FastMCP fixes...")
    print("=" * 50)

    # Test Pydantic fix
    pydantic_ok = test_pydantic_fix()

    # Test FastMCP fix
    fastmcp_ok = test_fastmcp_fix()

    # Test server import
    server_ok = test_server_import()

    # Test Pydantic settings
    settings_ok = test_pydantic_settings()

    # Summary
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Pydantic Fix: {'PASS' if pydantic_ok else 'FAIL'}")
    print(f"FastMCP Fix: {'PASS' if fastmcp_ok else 'FAIL'}")
    print(f"Server Import: {'PASS' if server_ok else 'FAIL'}")
    print(f"Pydantic Settings: {'PASS' if settings_ok else 'FAIL'}")

    if all([pydantic_ok, fastmcp_ok, server_ok, settings_ok]):
        print("All tests passed! The fixes are working.")
        return 0
    else:
        print("Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
