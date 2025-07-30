#!/usr/bin/env python3
"""Test script to verify Pydantic fix."""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_config_import():
    """Test that the config module can be imported without errors."""
    try:
        from mcp_graylog.config import config

        print("✅ Config import successful")
        return True
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False


def test_pydantic_settings():
    """Test that pydantic-settings can be imported."""
    try:
        from pydantic_settings import BaseSettings

        print("✅ pydantic-settings import successful")
        return True
    except ImportError as e:
        print(f"❌ pydantic-settings import failed: {e}")
        return False


def test_pydantic_field():
    """Test that pydantic Field can be imported."""
    try:
        from pydantic import Field

        print("✅ pydantic Field import successful")
        return True
    except ImportError as e:
        print(f"❌ pydantic Field import failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Pydantic fix...")
    print("=" * 40)

    tests = [
        test_pydantic_settings,
        test_pydantic_field,
        test_config_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed! The Pydantic fix is working.")
        return 0
    else:
        print("❌ Some tests failed. Please check the dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
