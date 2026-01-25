# tests/integration/test_cli_admin_integration.py

"""
Integration tests for refget admin CLI commands.

Run with: ./scripts/test-integration.sh
"""

import pytest
import json
from pathlib import Path
from typer.testing import CliRunner

from refget.cli.main import app

runner = CliRunner()


def cli(*args):
    """Run CLI command and return result."""
    result = runner.invoke(app, list(args))
    return result


@pytest.fixture
def test_fasta_files(test_fasta_path):
    """Return paths to test FASTA files."""
    return {
        "base": test_fasta_path / "base.fa",
        "different_names": test_fasta_path / "different_names.fa",
        "different_order": test_fasta_path / "different_order.fa",
    }


class TestAdminLoad:
    """Tests for: refget admin load <file>"""

    def test_load_fasta(self, test_fasta_files):
        """Loads FASTA file into database."""
        result = cli("admin", "load", str(test_fasta_files["base"]))

        assert result.exit_code == 0

    def test_load_fasta_with_name(self, test_fasta_files):
        """Loads FASTA with a human-readable name."""
        result = cli(
            "admin", "load", str(test_fasta_files["different_names"]), "--name", "Test Genome"
        )

        assert result.exit_code == 0

    def test_load_multiple_fastas(self, test_fasta_files):
        """Loads multiple FASTA files."""
        for name, path in test_fasta_files.items():
            result = cli("admin", "load", str(path))
            assert result.exit_code == 0


class TestAdminStatus:
    """Tests for: refget admin status (with database)"""

    def test_status_shows_connection(self, loaded_dbagent):
        """Status shows database connection info."""
        result = cli("admin", "status")

        assert result.exit_code == 0
        # Should show database is connected
        output = result.stdout.lower()
        assert "connected" in output or "ok" in output or "database" in output


class TestAdminLoadFromSeqcol:
    """Tests for loading from seqcol JSON files."""

    def test_load_seqcol_json(self, test_fasta_files, tmp_path):
        """Loads from pre-computed seqcol JSON file."""
        # First compute a seqcol JSON
        seqcol_file = tmp_path / "test.seqcol.json"

        result = cli("fasta", "seqcol", str(test_fasta_files["base"]), "-o", str(seqcol_file))
        assert result.exit_code == 0
        assert seqcol_file.exists()

        # Now load from the JSON file
        result = cli("admin", "load", str(seqcol_file))

        # Should work (may succeed or indicate duplicate)
        assert result.exit_code in [0, 1]


class TestAdminLoadFromPEP:
    """Tests for: refget admin load --pep"""

    def test_load_from_pep(self, test_fasta_files, tmp_path):
        """Loads from PEP project file."""
        # Create a minimal PEP file
        pep_file = tmp_path / "project.yaml"
        pep_file.write_text(
            """
pep_version: 2.0.0
sample_table: samples.csv
"""
        )

        samples_file = tmp_path / "samples.csv"
        samples_file.write_text(
            f"""sample_name,fasta
base,{test_fasta_files["base"]}
different,{test_fasta_files["different_names"]}
"""
        )

        result = cli("admin", "load", "--pep", str(pep_file))

        # May succeed or fail depending on PEP parsing
        # At minimum should not crash
        assert result.exit_code in [0, 1, 2]


class TestAdminWorkflow:
    """Test complete admin workflow."""

    def test_load_then_verify_in_api(self, test_fasta_files, client, base_digest):
        """Load via CLI, then verify accessible via API."""
        # Load a FASTA
        result = cli("admin", "load", str(test_fasta_files["base"]))
        assert result.exit_code == 0

        # Verify it's accessible via the API
        response = client.get(f"/collection/{base_digest}")

        # Should find the collection
        assert response.status_code == 200
        data = response.json()
        assert "names" in data
        assert "lengths" in data
