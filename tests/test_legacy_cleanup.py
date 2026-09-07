from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_run_server_py_removed():
    assert not (ROOT / "run_server.py").exists()


def test_start_sh_execs_packaged_cli_without_legacy_runner_or_stdio_noise():
    start_sh = (ROOT / "start.sh").read_text()

    assert start_sh.startswith("#!/bin/sh\n")
    assert "python -m mcp_graylog.server" not in start_sh
    assert "echo " not in start_sh
    assert "printf " not in start_sh
    assert "exec ./venv/bin/mcp-graylog" in start_sh
    assert "exec mcp-graylog" in start_sh


def test_init_exports_current_version_only():
    init_py = (ROOT / "mcp_graylog" / "__init__.py").read_text()

    assert '__version__ = "0.3.2"' in init_py
    assert "GraylogClient" not in init_py
    assert "__author__" not in init_py
    assert "__email__" not in init_py


def test_legacy_requests_client_and_tests_removed():
    assert not (ROOT / "mcp_graylog" / "client.py").exists()
    assert not (ROOT / "tests" / "test_client.py").exists()


def test_legacy_diagnostic_scripts_and_utils_removed():
    removed_paths = [
        "install_deps.sh",
        "test_entrypoint.sh",
        "test_fixes.py",
        "test_pydantic_fix.py",
        "mcp_graylog/utils.py",
        "tests/test_utils.py",
    ]

    for path in removed_paths:
        assert not (ROOT / path).exists()
