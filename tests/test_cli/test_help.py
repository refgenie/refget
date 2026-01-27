# tests/test_cli/test_help.py

"""Tests for CLI help output."""

import pytest


class TestHelpOutput:
    """Verify help text displays correctly."""

    def test_main_help(self, cli):
        """Main help shows all command groups."""
        result = cli("--help")

        assert result.exit_code == 0
        assert "config" in result.stdout.lower()
        assert "store" in result.stdout.lower()
        assert "fasta" in result.stdout.lower()
        assert "seqcol" in result.stdout.lower()
        assert "admin" in result.stdout.lower()

    def test_fasta_help(self, cli):
        """Fasta subcommand help."""
        result = cli("fasta", "--help")

        assert result.exit_code == 0
        assert "digest" in result.stdout.lower()
        assert "seqcol" in result.stdout.lower()

    def test_store_help(self, cli):
        """Store subcommand help."""
        result = cli("store", "--help")

        assert result.exit_code == 0
        assert "init" in result.stdout.lower()
        assert "add" in result.stdout.lower()

    def test_seqcol_help(self, cli):
        """Seqcol subcommand help."""
        result = cli("seqcol", "--help")

        assert result.exit_code == 0
        assert "compare" in result.stdout.lower()

    def test_config_help(self, cli):
        """Config subcommand help."""
        result = cli("config", "--help")

        assert result.exit_code == 0
        assert "show" in result.stdout.lower()

    def test_admin_help(self, cli):
        """Admin subcommand help."""
        result = cli("admin", "--help")

        assert result.exit_code == 0

    def test_command_help(self, cli):
        """Individual command help."""
        result = cli("fasta", "digest", "--help")

        assert result.exit_code == 0
        # Should mention file argument
        assert "file" in result.stdout.lower() or "path" in result.stdout.lower()

    def test_version(self, cli):
        """Version flag works."""
        result = cli("--version")

        assert result.exit_code == 0
        # Should show version number (e.g., "0.1.0")
        assert "." in result.stdout or "refget" in result.stdout.lower()


class TestHelpConsistency:
    """Verify help text is consistent and complete."""

    def test_all_subcommands_have_help(self, cli):
        """All major subcommands show help without error."""
        subcommands = ["fasta", "store", "seqcol", "config", "admin"]

        for cmd in subcommands:
            result = cli(cmd, "--help")
            assert result.exit_code == 0, f"Help failed for {cmd}: {result.stdout}"

    def test_help_mentions_usage(self, cli):
        """Help output includes usage information."""
        result = cli("--help")

        assert result.exit_code == 0
        # Typer typically shows "Usage:" in help
        assert "usage" in result.stdout.lower()
