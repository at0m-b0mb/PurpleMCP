"""Smoke tests for the CLI entry point."""

from typer.testing import CliRunner

from purplemcp import __version__
from purplemcp.cli import app

runner = CliRunner()


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_version_string_is_sane():
    parts = __version__.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)
