"""
Tests for CLI functionality.

Tests all CLI commands and their options.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import json
import tempfile
from mudipu.cli.main import cli


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def temp_trace_file():
    """Create a temporary trace file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # Create minimal valid session
        session_data = {
            "session_id": "550e8400-e29b-41d4-a716-446655440001",
            "trace_id": "550e8400-e29b-41d4-a716-446655440002",
            "name": "test-session",
            "created_at": "2026-03-30T10:00:00",
            "ended_at": "2026-03-30T10:01:00",
            "tags": [],
            "metadata": {"user_input": "Hello"},
            "turns": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "turn_number": 1,
                    "timestamp": "2026-03-30T10:00:30",
                    "request_messages": [{"role": "user", "content": "Hello"}],
                    "response_message": {"role": "assistant", "content": "Hi there"},
                    "request_tools": [],
                    "tool_calls_detected": [],
                    "has_tool_calls": False,
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                    "duration_ms": 500,
                    "model": "gpt-4",
                }
            ],
            "turn_count": 1,
            "total_tokens": 15,
            "total_duration_ms": 500,
        }
        json.dump(session_data, f)
        return Path(f.name)


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test main CLI help."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Mudipu" in result.output
        assert "Commands:" in result.output

    def test_cli_version(self, runner):
        """Test version command."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower()


class TestStatsCommand:
    """Test stats command."""

    def test_stats_help(self, runner):
        """Test stats command help."""
        result = runner.invoke(cli, ["stats", "--help"])

        assert result.exit_code == 0
        assert "statistics" in result.output.lower()

    def test_stats_execution(self, runner, temp_trace_file):
        """Test stats command execution."""
        result = runner.invoke(cli, ["stats", str(temp_trace_file)])

        # Should execute without error
        assert result.exit_code == 0
        # Should show session info
        assert "test-session" in result.output or "550e8400" in result.output


class TestAnalyzeCommand:
    """Test analyze command."""

    def test_analyze_help(self, runner):
        """Test analyze command help."""
        result = runner.invoke(cli, ["analyze", "--help"])

        assert result.exit_code == 0
        assert "summary" in result.output.lower()

    def test_analyze_execution(self, runner, temp_trace_file):
        """Test analyze command execution."""
        result = runner.invoke(cli, ["analyze", str(temp_trace_file)])

        assert result.exit_code == 0
        # Should generate some output
        assert len(result.output) > 0


class TestHealthCommand:
    """Test health command."""

    def test_health_help(self, runner):
        """Test health command help."""
        result = runner.invoke(cli, ["health", "--help"])

        assert result.exit_code == 0
        assert "health" in result.output.lower()
        assert "--threshold" in result.output
        assert "--visualize" in result.output
        assert "--goal" in result.output

    def test_health_execution_without_deps(self, runner, temp_trace_file):
        """Test health command when dependencies not installed."""
        # This may fail if health dependencies not installed
        result = runner.invoke(cli, ["health", str(temp_trace_file)])

        # Should either succeed or show dependency error
        assert "health" in result.output.lower() or "install" in result.output.lower()

    def test_health_with_threshold(self, runner, temp_trace_file):
        """Test health command with custom threshold."""
        result = runner.invoke(cli, ["health", str(temp_trace_file), "--threshold", "0.6"])

        # Should accept threshold option
        assert "--threshold" not in result.output  # No error about unknown option

    def test_health_with_goal(self, runner, temp_trace_file):
        """Test health command with goal specification."""
        result = runner.invoke(cli, ["health", str(temp_trace_file), "--goal", "Test goal"])

        # Should accept goal option
        assert "--goal" not in result.output  # No error about unknown option


class TestExportHTMLCommand:
    """Test export-html command."""

    def test_export_html_help(self, runner):
        """Test export-html command help."""
        result = runner.invoke(cli, ["export-html", "--help"])

        assert result.exit_code == 0
        assert "html" in result.output.lower()

    def test_export_html_execution(self, runner, temp_trace_file):
        """Test export-html command execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "output.html"

            result = runner.invoke(cli, ["export-html", str(temp_trace_file), "-o", str(output_file)])

            # Should execute
            assert result.exit_code == 0


class TestListTracesCommand:
    """Test list-traces command."""

    def test_list_traces_help(self, runner):
        """Test list-traces command help."""
        result = runner.invoke(cli, ["list-traces", "--help"])

        assert result.exit_code == 0
        assert "list" in result.output.lower()

    def test_list_traces_empty_dir(self, runner):
        """Test list-traces on empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(cli, ["list-traces", tmpdir])

            assert result.exit_code == 0
            assert "No trace files found" in result.output or result.output.strip() == ""

    def test_list_traces_with_files(self, runner, temp_trace_file):
        """Test list-traces with actual trace file."""
        result = runner.invoke(cli, ["list-traces", str(temp_trace_file.parent)])

        assert result.exit_code == 0
        # Should list the file
        assert temp_trace_file.name in result.output or len(result.output) > 0


class TestConfigCommand:
    """Test config commands."""

    def test_config_help(self, runner):
        """Test config command help."""
        result = runner.invoke(cli, ["config", "--help"])

        assert result.exit_code == 0
        assert "config" in result.output.lower()

    def test_config_show(self, runner):
        """Test config show command."""
        result = runner.invoke(cli, ["config", "show"])

        # Should execute
        assert result.exit_code == 0

    def test_config_init(self, runner):
        """Test config init command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "mudipu.yaml"

            result = runner.invoke(cli, ["config", "init", str(config_file)])

            # Should create config file
            assert result.exit_code == 0


class TestVersionCommand:
    """Test version command."""

    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower() or "mudipu" in result.output.lower()


class TestErrorHandling:
    """Test error handling in CLI."""

    def test_nonexistent_file(self, runner):
        """Test CLI with nonexistent file."""
        result = runner.invoke(cli, ["stats", "/nonexistent/file.json"])

        # Should fail gracefully
        assert result.exit_code != 0

    def test_invalid_json_file(self, runner):
        """Test CLI with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json{]}")
            temp_file = Path(f.name)

        result = runner.invoke(cli, ["stats", str(temp_file)])

        # Should fail gracefully
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
