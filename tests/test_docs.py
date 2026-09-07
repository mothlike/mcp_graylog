from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_current_docs(text: str) -> None:
    assert "GRAYLOG_TOKEN" in text
    assert "/api/search/messages" in text
    assert "/api/search/aggregate" in text
    assert "/api/streams" in text
    assert "/api/streams/{stream_id}" in text
    assert "/api/system" in text
    assert "MCP_SERVER_ALLOWED_HOSTS" in text
    assert "/health_check" not in text
    assert "python -m mcp_graylog.server" not in text
    assert "/api/search/universal" not in text


def test_readme_documents_current_codex_and_graylog_api() -> None:
    text = read_text("README.md")

    assert "[mcp_servers.graylog]" in text
    assert 'command = "uv"' in text
    assert 'args = ["run", "mcp-graylog"]' in text
    assert "Codex stdio" in text
    assert "Streamable HTTP" in text
    assert_current_docs(text)


def test_documentation_is_current_reference() -> None:
    text = read_text("DOCUMENTATION.md")

    assert "Codex stdio" in text
    assert "Streamable HTTP" in text
    assert_current_docs(text)


def test_docs_include_beginner_dependency_installation() -> None:
    combined = "\n".join(
        read_text(path)
        for path in (
            "README.md",
            "DOCUMENTATION.md",
        )
    )

    for expected in (
        "Python 3.11",
        "brew install python@3.11 uv",
        "python3 -m pip install --user uv",
        "uv venv venv --python 3.11",
        "source venv/bin/activate",
        "uv pip install -e .",
        'uv pip install -e ".[dev]"',
        "uv run mcp-graylog --help",
        "uv run pytest -q",
    ):
        assert expected in combined


def test_client_configuration_examples_cover_common_mcp_clients() -> None:
    combined = "\n".join(
        read_text(path)
        for path in (
            "README.md",
            "DOCUMENTATION.md",
            "test_cursor_integration.py",
        )
    )

    for expected in (
        "~/.codex/config.toml",
        "Claude Code",
        ".mcp.json",
        "claude mcp add-json",
        "Cursor",
        ".cursor/mcp.json",
        "OpenCode",
        "opencode.jsonc",
        '"type": "local"',
        '"environment"',
        "Hermes",
        "~/.hermes/config.yaml",
        "mcp_servers",
        "OpenClaw",
        "~/.openclaw/openclaw.json",
        "openclaw mcp set",
        '"servers"',
    ):
        assert expected in combined


def test_env_example_is_token_first_stdio_config() -> None:
    text = read_text("env.example")

    assert "GRAYLOG_TOKEN" in text
    assert "MCP_SERVER_TRANSPORT=stdio" in text
    assert "MCP_SERVER_DNS_REBINDING_PROTECTION=true" in text
    assert "MCP_SERVER_ALLOWED_HOSTS=" in text
    assert "GRAYLOG_PASSWORD" not in text


def test_examples_and_setup_exclude_legacy_configuration() -> None:
    combined = "\n".join(
        read_text(path)
        for path in (
            "examples/basic_usage.py",
            "example_setup.sh",
            "test_cursor_integration.py",
        )
    )

    assert "GRAYLOG_TOKEN" in combined
    assert "GRAYLOG_PASSWORD" not in combined
    assert "/health_check" not in combined
    assert "python -m mcp_graylog.server" not in combined
    assert "/api/search/universal" not in combined
