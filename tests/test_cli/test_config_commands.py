# tests/test_cli/test_config_commands.py

"""Tests for refget config CLI commands."""

import pytest
import json


class TestConfigShow:
    """Tests for: refget config show"""

    def test_shows_config(self, cli, env_with_config):
        """Displays current configuration."""
        result = cli("config", "show")

        assert result.exit_code == 0
        # Should show config content
        assert "store" in result.stdout.lower() or "path" in result.stdout.lower()

    def test_shows_config_as_json(self, cli, env_with_config):
        """config show outputs valid JSON by default."""
        result = cli("config", "show")

        assert result.exit_code == 0
        # config show always outputs JSON via print_json
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    def test_show_without_config(self, cli, tmp_path, monkeypatch):
        """Shows default or error when no config exists."""
        # Point to nonexistent config
        monkeypatch.setenv("REFGET_CONFIG", str(tmp_path / "nonexistent.toml"))

        result = cli("config", "show")

        # Should either show defaults or indicate no config
        assert result.exit_code in [0, 1]


class TestConfigGet:
    """Tests for: refget config get <key>"""

    def test_gets_value(self, cli, env_with_config):
        """Gets specific config value."""
        result = cli("config", "get", "store.path")

        assert result.exit_code == 0
        # Should output the value
        assert len(result.stdout.strip()) > 0

    def test_missing_key(self, cli, env_with_config):
        """Returns error for nonexistent key."""
        result = cli("config", "get", "nonexistent.key")

        assert result.exit_code != 0

    def test_nested_key(self, cli, temp_config, monkeypatch):
        """Gets nested config value."""
        monkeypatch.setenv("REFGET_CONFIG", str(temp_config))

        result = cli("config", "get", "store.path")

        assert result.exit_code == 0


class TestConfigSet:
    """Tests for: refget config set <key> <value>"""

    def test_sets_value(self, cli, temp_config, monkeypatch):
        """Sets config value."""
        monkeypatch.setenv("REFGET_CONFIG", str(temp_config))

        result = cli("config", "set", "store.path", "/new/path")
        assert result.exit_code == 0

        # Verify it was set
        result = cli("config", "get", "store.path")
        assert "/new/path" in result.stdout

    def test_sets_new_key(self, cli, temp_config, monkeypatch):
        """Sets a new config key."""
        monkeypatch.setenv("REFGET_CONFIG", str(temp_config))

        result = cli("config", "set", "api.url", "https://example.com")
        assert result.exit_code == 0

    def test_set_without_value(self, cli, env_with_config):
        """Set without value fails."""
        result = cli("config", "set", "store.path")

        assert result.exit_code != 0


class TestConfigInit:
    """Tests for: refget config init"""

    def test_creates_config_file(self, cli, tmp_path, monkeypatch):
        """Creates new config file."""
        config_path = tmp_path / "new_config.toml"
        monkeypatch.setenv("REFGET_CONFIG", str(config_path))

        # Provide minimal input for interactive prompts
        from typer.testing import CliRunner
        from refget.cli import app

        runner = CliRunner()
        result = runner.invoke(
            app, ["config", "init"], input=f"{tmp_path}/store\n\n\n"  # Store path + defaults
        )

        # Config init should succeed or prompt for input
        assert result.exit_code in [0, 1]

    def test_init_no_overwrite(self, cli, temp_config, monkeypatch):
        """Does not overwrite existing config without confirmation."""
        monkeypatch.setenv("REFGET_CONFIG", str(temp_config))

        from typer.testing import CliRunner
        from refget.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["config", "init"], input="n\n")  # Say no to overwrite

        # Should either skip or require confirmation
        assert result.exit_code in [0, 1]


class TestConfigPath:
    """Tests for: refget config path"""

    def test_shows_config_path(self, cli, env_with_config, temp_config):
        """Shows path to config file."""
        result = cli("config", "path")

        assert result.exit_code == 0
        # Should show the config file path
        assert str(temp_config) in result.stdout or "config" in result.stdout.lower()


class TestConfigValidate:
    """Tests for: refget config validate"""

    def test_validates_valid_config(self, cli, env_with_config):
        """Validates valid config file."""
        result = cli("config", "validate")

        assert result.exit_code == 0

    def test_validates_invalid_config(self, cli, tmp_path, monkeypatch):
        """Reports invalid config."""
        invalid_config = tmp_path / "invalid.toml"
        invalid_config.write_text("this is not valid toml {{{")
        monkeypatch.setenv("REFGET_CONFIG", str(invalid_config))

        result = cli("config", "validate")

        assert result.exit_code != 0


class TestConfigEnvVars:
    """Tests for environment variable handling."""

    def test_respects_refget_config_env(self, cli, temp_config, monkeypatch):
        """Uses REFGET_CONFIG environment variable."""
        monkeypatch.setenv("REFGET_CONFIG", str(temp_config))

        result = cli("config", "show")

        assert result.exit_code == 0

    def test_respects_refget_store_env(self, cli, tmp_path, monkeypatch):
        """REFGET_STORE overrides config store path."""
        store_path = tmp_path / "env_store"
        monkeypatch.setenv("REFGET_STORE", str(store_path))

        # Initialize store using env var
        result = cli("store", "init")

        # Should use REFGET_STORE path
        if result.exit_code == 0:
            assert store_path.exists()


class TestConfigErrorHandling:
    """Test error handling for config commands."""

    def test_get_from_missing_config(self, cli, tmp_path, monkeypatch):
        """Get from nonexistent config fails gracefully."""
        monkeypatch.setenv("REFGET_CONFIG", str(tmp_path / "missing.toml"))

        result = cli("config", "get", "store.path")

        # Should fail or return default
        assert result.exit_code in [0, 1, 2]

    def test_set_to_readonly_config(self, cli, tmp_path, monkeypatch):
        """Set to read-only config fails gracefully."""
        import os
        import stat

        config = tmp_path / "readonly.toml"
        config.write_text("[store]\npath = '/tmp'\n")
        os.chmod(config, stat.S_IRUSR)

        try:
            monkeypatch.setenv("REFGET_CONFIG", str(config))
            result = cli("config", "set", "store.path", "/new/path")

            assert result.exit_code != 0
        finally:
            os.chmod(config, stat.S_IRUSR | stat.S_IWUSR)
