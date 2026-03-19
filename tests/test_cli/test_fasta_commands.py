# tests/test_cli/test_fasta_commands.py

"""
Tests for refget fasta CLI commands.

These test CLI-specific behavior: output formatting, exit codes, argument parsing.
"""

import importlib.util
import json
import os
from pathlib import Path

_conftest_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conftest.py"
)
_spec = importlib.util.spec_from_file_location("tests_conftest", _conftest_path)
_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_conftest)

BASE_FASTA = _conftest.BASE_FASTA
DIFFERENT_NAMES_FASTA = _conftest.DIFFERENT_NAMES_FASTA
TEST_FASTA_DIGESTS = _conftest.TEST_FASTA_DIGESTS
assert_json_output = _conftest.assert_json_output
assert_valid_digest = _conftest.assert_valid_digest


class TestFastaDigest:
    """Tests for: refget fasta digest <file>"""

    def test_known_digest(self, cli):
        """Verify digest matches expected value for known file."""
        result = cli("fasta", "digest", str(BASE_FASTA))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        expected_digest = TEST_FASTA_DIGESTS["base.fa"]["top_level_digest"]
        assert data["digest"] == expected_digest

    def test_gzipped_file(self, cli, sample_fasta_gz):
        """Handles gzipped files seamlessly."""
        result = cli("fasta", "digest", str(sample_fasta_gz))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "digest" in data

    def test_file_not_found_exit_code(self, cli):
        """Returns non-zero exit code for missing file."""
        result = cli("fasta", "digest", "/nonexistent/file.fa")
        assert result.exit_code != 0

    def test_different_files_different_digests(self, cli):
        """Different files produce different digests."""
        result1 = cli("fasta", "digest", str(BASE_FASTA))
        result2 = cli("fasta", "digest", str(DIFFERENT_NAMES_FASTA))

        digest1 = json.loads(result1.stdout)["digest"]
        digest2 = json.loads(result2.stdout)["digest"]
        assert digest1 != digest2


class TestFastaSeqcol:
    """Tests for: refget fasta seqcol <file>"""

    def test_known_seqcol(self, cli):
        """Verify seqcol matches expected values for known file."""
        result = cli("fasta", "seqcol", str(BASE_FASTA))

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        expected = TEST_FASTA_DIGESTS["base.fa"]["level2"]
        assert data["names"] == expected["names"]
        assert data["lengths"] == expected["lengths"]

    def test_output_to_file(self, cli, sample_fasta, tmp_path):
        """Writes to file with -o option."""
        output = tmp_path / "out.seqcol.json"
        result = cli("fasta", "seqcol", str(sample_fasta), "-o", str(output))

        assert result.exit_code == 0
        assert output.exists()
        data = json.loads(output.read_text())
        assert "names" in data


class TestFastaFai:
    """Tests for: refget fasta fai <file>"""

    def test_fai_sequence_count(self, cli, multi_seq_fasta, tmp_path):
        """FAI has one line per sequence."""
        output = tmp_path / "test.fa.fai"
        result = cli("fasta", "fai", str(multi_seq_fasta), "-o", str(output))

        assert result.exit_code == 0
        lines = output.read_text().strip().split("\n")
        assert len(lines) == 3  # multi_seq_fasta has 3 sequences


class TestFastaChromSizes:
    """Tests for: refget fasta chrom-sizes <file>"""

    def test_chrom_sizes_values(self, cli):
        """Verify chrom.sizes values for known file."""
        result = cli("fasta", "chrom-sizes", str(BASE_FASTA))

        assert result.exit_code == 0
        sizes = {}
        for line in result.stdout.strip().split("\n"):
            name, length = line.split("\t")
            sizes[name] = int(length)

        assert sizes.get("chrX") == 8
        assert sizes.get("chr1") == 4
        assert sizes.get("chr2") == 4


class TestFastaIndex:
    """Tests for: refget fasta index <file>"""

    def test_index_creates_all_files(self, cli, sample_fasta):
        """Index with --json lists all 5 created files."""
        result = cli("fasta", "index", str(sample_fasta), "--json")

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data["files_created"]) == 5
        extensions = [Path(f).suffix for f in data["files_created"]]
        assert ".fai" in extensions
        assert ".json" in extensions
        assert ".rgsi" in extensions
        assert ".rgci" in extensions


class TestFastaStats:
    """Tests for: refget fasta stats <file>"""

    def test_stats_known_file(self, cli):
        """Stats for known test file."""
        result = cli("fasta", "stats", str(BASE_FASTA), "--json")

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # base.fa: chrX(8), chr1(4), chr2(4) = 16 total
        assert data["sequences"] == 3
        assert data["total_length"] == 16

    def test_stats_plain_output(self, cli, sample_fasta):
        """Stats can output in plain text format."""
        result = cli("fasta", "stats", str(sample_fasta))

        assert result.exit_code == 0
        assert len(result.stdout.strip()) > 0


class TestFastaValidate:
    """Tests for: refget fasta validate <file>"""

    def test_valid_fasta(self, cli, sample_fasta):
        """Valid FASTA passes validation."""
        result = cli("fasta", "validate", str(sample_fasta))
        assert result.exit_code == 0

    def test_invalid_fasta_exits_nonzero(self, cli, tmp_path):
        """Invalid FASTA fails validation."""
        invalid = tmp_path / "invalid.fa"
        invalid.write_text("This is not a valid FASTA file\nNo headers here\n")
        result = cli("fasta", "validate", str(invalid))
        assert result.exit_code != 0


class TestFastaRgsi:
    """Tests for: refget fasta rgsi <file>"""

    def test_rgsi_format_and_content(self, cli, sample_fasta):
        """Creates .rgsi with correct headers, columns, and sequence data."""
        result = cli("fasta", "rgsi", str(sample_fasta))

        assert result.exit_code == 0
        rgsi_path = sample_fasta.parent / f"{sample_fasta.stem}.rgsi"
        assert rgsi_path.exists()

        content = rgsi_path.read_text()
        assert "##seqcol_digest=" in content
        assert "#name\tlength\talphabet\tsha512t24u\tmd5\tdescription" in content

        data_lines = [line for line in content.strip().split("\n") if not line.startswith("#")]
        assert len(data_lines) == 2  # sample_fasta has 2 sequences

        # Verify first sequence
        cols = data_lines[0].split("\t")
        assert len(cols) == 6
        assert cols[0] == "chr1"
        assert cols[1] == "8"

    def test_rgsi_custom_output(self, cli, sample_fasta, tmp_path):
        """Writes to a custom output path with -o."""
        custom_output = tmp_path / "custom.rgsi"
        result = cli("fasta", "rgsi", str(sample_fasta), "-o", str(custom_output))

        assert result.exit_code == 0
        assert custom_output.exists()


class TestFastaRgci:
    """Tests for: refget fasta rgci <file>"""

    def test_rgci_format_and_digest(self, cli, sample_fasta):
        """Creates .rgci with correct columns, and digest matches fasta digest."""
        # Get expected digest
        digest_result = cli("fasta", "digest", str(sample_fasta))
        expected_digest = json.loads(digest_result.stdout)["digest"]

        # Generate RGCI
        result = cli("fasta", "rgci", str(sample_fasta))
        assert result.exit_code == 0

        rgci_path = sample_fasta.parent / f"{sample_fasta.stem}.rgci"
        content = rgci_path.read_text()
        lines = content.strip().split("\n")

        # Header has 8 columns
        header_cols = lines[0].lstrip("#").split("\t")
        assert len(header_cols) == 8
        assert header_cols[0] == "digest"

        # Data row: correct column count, digest matches, n_sequences correct
        data_cols = lines[1].split("\t")
        assert len(data_cols) == 8
        assert data_cols[0] == expected_digest
        assert data_cols[1] == "2"  # sample_fasta has 2 sequences
