# tests/test_cli/test_help.py

"""Tests for CLI help output."""

import pytest


class TestHelpOutput:
    """Verify help text displays correctly."""

    def test_main_help_shows_all_groups(self, cli):
        """Main help shows all command groups and usage information."""
        result = cli("--help")

        assert result.exit_code == 0
        assert "config" in result.stdout.lower()
        assert "store" in result.stdout.lower()
        assert "fasta" in result.stdout.lower()
        assert "seqcol" in result.stdout.lower()
        assert "admin" in result.stdout.lower()
        # Typer typically shows "Usage:" in help
        assert "usage" in result.stdout.lower()

    @pytest.mark.parametrize("cmd", ["fasta", "store", "seqcol", "config", "admin"])
    def test_all_subcommands_have_help(self, cli, cmd):
        """All major subcommands show help without error."""
        result = cli(cmd, "--help")
        assert result.exit_code == 0, f"Help failed for {cmd}: {result.stdout}"

    def test_version(self, cli):
        """Version flag works."""
        result = cli("--version")

        assert result.exit_code == 0
        # Should show version number (e.g., "0.1.0")
        assert "." in result.stdout or "refget" in result.stdout.lower()
