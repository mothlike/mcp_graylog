import tomllib
from importlib.metadata import EntryPoint
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_uses_official_mcp_sdk_and_httpx():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dependencies = data["project"]["dependencies"]

    assert "mcp[cli]>=2.1,<3" in dependencies
    assert "httpx>=0.27.0" in dependencies
    assert all(not dep.startswith("fastmcp") for dep in dependencies)
    assert all(not dep.startswith("requests") for dep in dependencies)


def test_pyproject_exposes_mcp_graylog_console_script():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert data["project"]["scripts"]["mcp-graylog"] == "mcp_graylog.cli:main"

    entrypoint = EntryPoint(
        name="mcp-graylog",
        value=data["project"]["scripts"]["mcp-graylog"],
        group="console_scripts",
    )
    assert callable(entrypoint.load())


def test_requirements_match_runtime_dependencies():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    pyproject_deps = set(data["project"]["dependencies"])
    requirements = {
        line.strip()
        for line in (ROOT / "requirements.txt").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    assert requirements == pyproject_deps
