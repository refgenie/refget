# tests/test_cli/test_admin_commands.py

"""
Tests for refget admin CLI commands.

These are unit tests that do NOT require database access.
Database-dependent admin tests are in tests/integration/test_cli_admin_integration.py
"""


class TestAdminStatus:
    """Tests for: refget admin status

    Note: status command requires database connection.
    Database-dependent tests are in tests/integration/test_cli_admin_integration.py
    """

    def test_shows_config_info(self, cli):
        """Shows database configuration information even without connection."""
        result = cli("admin", "status")

        # Should show configuration info regardless of connection
        # (exit code may be 1 if database connection fails)
        assert "Host:" in result.stdout or "Database" in result.stdout.lower()


class TestAdminInfo:
    """Tests for: refget admin info"""

    def test_shows_info(self, cli):
        """Shows system/installation info."""
        result = cli("admin", "info")

        assert result.exit_code == 0
        # Should show version or configuration info
        assert "version" in result.stdout.lower() or "refget" in result.stdout.lower()

    def test_info_shows_dependencies(self, cli):
        """Shows dependency information."""
        result = cli("admin", "info")

        assert result.exit_code == 0
        # Should show dependencies section
        assert "dependencies" in result.stdout.lower() or "gtars" in result.stdout.lower()


class TestAdminErrorHandling:
    """Test error handling for admin commands."""

    def test_load_nonexistent_file(self, cli):
        """Load nonexistent file fails gracefully."""
        result = cli("admin", "load", "/nonexistent/file.fa")

        assert result.exit_code != 0
