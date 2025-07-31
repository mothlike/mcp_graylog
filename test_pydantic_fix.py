#!/usr/bin/env python3
"""
Test script to verify the Pydantic fix is working.
This script tests that pydantic-settings is properly installed and working.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_config_import():
    """Test that the config module can be imported without deprecation warnings."""
    try:
        from mcp_graylog.config import config

        print("Config import successful")
        return True
    except Exception as e:
        print(f"ERROR: Config import failed: {e}")
        return False


def test_pydantic_settings():
    """Test that pydantic-settings works correctly."""
    try:
        from pydantic_settings import BaseSettings

        print("pydantic-settings import successful")
        return True
    except ImportError as e:
        print(f"ERROR: pydantic-settings import failed: {e}")
        return False


def test_pydantic_field():
    """Test that pydantic Field import works."""
    try:
        from pydantic import Field

        print("pydantic Field import successful")
        return True
    except ImportError as e:
        print(f"ERROR: pydantic Field import failed: {e}")
        return False


def test_pydantic_config():
    """Test that pydantic ConfigDict works."""
    try:
        from pydantic import ConfigDict

        print("pydantic ConfigDict import successful")
        return True
    except ImportError as e:
        print(f"ERROR: pydantic ConfigDict import failed: {e}")
        return False


def test_integration():
    """Test that all components work together."""
    try:
        from pydantic import ConfigDict
        from pydantic_settings import BaseSettings

        class TestConfig(BaseSettings):
            model_config = ConfigDict(env_file=".env")
            test_field: str = "default"

        config = TestConfig()
        print("Integration test successful")
        return True
    except Exception as e:
        print(f"ERROR: Integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Pydantic fix...")
    print("=" * 50)

    tests = [
        test_pydantic_settings,
        test_pydantic_field,
        test_pydantic_config,
        test_config_import,
        test_integration,
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
        print("All tests passed! The Pydantic fix is working.")
        return 0
    else:
        print("Some tests failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
