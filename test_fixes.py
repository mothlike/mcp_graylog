#!/usr/bin/env python3
"""Test script to verify Pydantic and FastMCP fixes."""

import sys
import os
import warnings

# Suppress deprecation warnings for testing
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_config_import():
    """Test that the config module can be imported without deprecation warnings."""
    try:
        from mcp_graylog.config import config

        print("✅ Config import successful (no deprecation warnings)")
        return True
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False


def test_fastmcp_import():
    """Test that FastMCP can be imported and initialized."""
    try:
        from fastmcp import FastMCP

        app = FastMCP("test")
        print("✅ FastMCP import and initialization successful")
        return True
    except Exception as e:
        print(f"❌ FastMCP import failed: {e}")
        return False


def test_server_import():
    """Test that the server module can be imported."""
    try:
        # Import without running the server
        import mcp_graylog.server

        print("✅ Server module import successful")
        return True
    except Exception as e:
        print(f"❌ Server module import failed: {e}")
        return False


def test_pydantic_settings():
    """Test that pydantic-settings works correctly."""
    try:
        from pydantic_settings import BaseSettings
        from pydantic import ConfigDict

        class TestConfig(BaseSettings):
            test_field: str = "default"
            model_config = ConfigDict(env_prefix="TEST_")

        config = TestConfig()
        print("✅ Pydantic settings with ConfigDict works")
        return True
    except Exception as e:
        print(f"❌ Pydantic settings test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Pydantic and FastMCP fixes...")
    print("=" * 50)

    tests = [
        test_pydantic_settings,
        test_config_import,
        test_fastmcp_import,
        test_server_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed! The fixes are working.")
        return 0
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
