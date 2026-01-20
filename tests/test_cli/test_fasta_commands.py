# tests/test_cli/test_fasta_commands.py

"""
Tests for refget fasta CLI commands.

These test the CLI wrapper behavior: output formatting, exit codes, argument parsing.
"""

import pytest
import json
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conftest import (
    BASE_FASTA,
    DIFFERENT_NAMES_FASTA,
    TEST_FASTA_DIGESTS,
    assert_json_output,
    assert_valid_digest,
)


class TestFastaDigest:
    """Tests for: refget fasta digest <file>"""

    def test_outputs_json(self, cli, sample_fasta):
        """Output is valid JSON with digest."""
        result = cli("fasta", "digest", str(sample_fasta))

        data = assert_json_output(result, ["digest"])
        assert_valid_digest(data["digest"])

    def test_digest_with_file_key(self, cli, sample_fasta):
        """Output may include file path."""
        result = cli("fasta", "digest", str(sample_fasta))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "digest" in data

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
        # Error message goes to stderr (correct Unix behavior)
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_missing_argument(self, cli):
        """Returns non-zero exit for missing argument."""
        result = cli("fasta", "digest")

        assert result.exit_code != 0

    def test_known_digest(self, cli):
        """Verify digest matches expected value for known file."""
        result = cli("fasta", "digest", str(BASE_FASTA))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        expected_digest = TEST_FASTA_DIGESTS["base.fa"]["top_level_digest"]
        assert data["digest"] == expected_digest

    def test_different_files_different_digests(self, cli):
        """Different files produce different digests."""
        result1 = cli("fasta", "digest", str(BASE_FASTA))
        result2 = cli("fasta", "digest", str(DIFFERENT_NAMES_FASTA))

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        digest1 = json.loads(result1.stdout)["digest"]
        digest2 = json.loads(result2.stdout)["digest"]
        assert digest1 != digest2


class TestFastaSeqcol:
    """Tests for: refget fasta seqcol <file>"""

    def test_outputs_seqcol_json(self, cli, sample_fasta):
        """Output is valid seqcol JSON."""
        result = cli("fasta", "seqcol", str(sample_fasta))

        data = assert_json_output(result, ["names", "lengths", "sequences"])
        assert isinstance(data["names"], list)
        assert isinstance(data["lengths"], list)
        assert isinstance(data["sequences"], list)

    def test_seqcol_array_lengths_match(self, cli, sample_fasta):
        """All seqcol arrays have same length."""
        result = cli("fasta", "seqcol", str(sample_fasta))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        n_seqs = len(data["names"])
        assert len(data["lengths"]) == n_seqs
        assert len(data["sequences"]) == n_seqs

    def test_output_to_file(self, cli, sample_fasta, tmp_path):
        """Writes to file with -o option."""
        output = tmp_path / "out.seqcol.json"
        result = cli("fasta", "seqcol", str(sample_fasta), "-o", str(output))

        assert result.exit_code == 0
        assert output.exists()

        data = json.loads(output.read_text())
        assert "names" in data
        assert "lengths" in data
        assert "sequences" in data

    def test_known_seqcol(self, cli):
        """Verify seqcol matches expected values for known file."""
        result = cli("fasta", "seqcol", str(BASE_FASTA))

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        expected = TEST_FASTA_DIGESTS["base.fa"]["level2"]
        assert data["names"] == expected["names"]
        assert data["lengths"] == expected["lengths"]

    def test_gzipped_file(self, cli, sample_fasta_gz):
        """Handles gzipped FASTA files."""
        result = cli("fasta", "seqcol", str(sample_fasta_gz))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "names" in data


class TestFastaFai:
    """Tests for: refget fasta fai <file>"""

    def test_outputs_fai_format(self, cli, sample_fasta, tmp_path):
        """Outputs valid FAI format."""
        output = tmp_path / "test.fa.fai"
        result = cli("fasta", "fai", str(sample_fasta), "-o", str(output))

        assert result.exit_code == 0
        assert output.exists()

        # FAI format: name\tlength\toffset\tline_bases\tline_width
        lines = output.read_text().strip().split("\n")
        assert len(lines) > 0
        for line in lines:
            parts = line.split("\t")
            assert len(parts) >= 2  # At least name and length

    def test_fai_to_stdout(self, cli, sample_fasta):
        """Outputs FAI to stdout when no -o specified."""
        result = cli("fasta", "fai", str(sample_fasta))

        assert result.exit_code == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) > 0

    def test_fai_sequence_count(self, cli, multi_seq_fasta, tmp_path):
        """FAI has one line per sequence."""
        output = tmp_path / "test.fa.fai"
        result = cli("fasta", "fai", str(multi_seq_fasta), "-o", str(output))

        assert result.exit_code == 0
        lines = output.read_text().strip().split("\n")
        assert len(lines) == 3  # multi_seq_fasta has 3 sequences


class TestFastaChromSizes:
    """Tests for: refget fasta chrom-sizes <file>"""

    def test_outputs_chrom_sizes(self, cli, sample_fasta, tmp_path):
        """Outputs valid chrom.sizes format."""
        output = tmp_path / "test.chrom.sizes"
        result = cli("fasta", "chrom-sizes", str(sample_fasta), "-o", str(output))

        assert result.exit_code == 0
        assert output.exists()

        # Format: name\tlength
        lines = output.read_text().strip().split("\n")
        for line in lines:
            parts = line.split("\t")
            assert len(parts) == 2
            assert parts[1].isdigit()

    def test_chrom_sizes_to_stdout(self, cli, sample_fasta):
        """Outputs chrom.sizes to stdout when no -o specified."""
        result = cli("fasta", "chrom-sizes", str(sample_fasta))

        assert result.exit_code == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) > 0
        for line in lines:
            parts = line.split("\t")
            assert len(parts) == 2

    def test_chrom_sizes_values(self, cli):
        """Verify chrom.sizes values for known file."""
        result = cli("fasta", "chrom-sizes", str(BASE_FASTA))

        assert result.exit_code == 0
        lines = result.stdout.strip().split("\n")

        # base.fa has chrX(8), chr1(4), chr2(4)
        sizes = {}
        for line in lines:
            name, length = line.split("\t")
            sizes[name] = int(length)

        assert sizes.get("chrX") == 8
        assert sizes.get("chr1") == 4
        assert sizes.get("chr2") == 4


class TestFastaIndex:
    """Tests for: refget fasta index <file>"""

    def test_creates_fai_file(self, cli, sample_fasta):
        """Creates .fai file."""
        result = cli("fasta", "index", str(sample_fasta))

        assert result.exit_code == 0
        fai_path = Path(str(sample_fasta) + ".fai")
        assert fai_path.exists()

    def test_creates_seqcol_file(self, cli, sample_fasta):
        """Creates .seqcol.json file."""
        result = cli("fasta", "index", str(sample_fasta))

        assert result.exit_code == 0
        seqcol_path = sample_fasta.parent / f"{sample_fasta.stem}.seqcol.json"
        assert seqcol_path.exists()

        data = json.loads(seqcol_path.read_text())
        assert "names" in data

    def test_creates_chrom_sizes_file(self, cli, sample_fasta):
        """Creates .chrom.sizes file."""
        result = cli("fasta", "index", str(sample_fasta))

        assert result.exit_code == 0
        sizes_path = sample_fasta.parent / f"{sample_fasta.stem}.chrom.sizes"
        assert sizes_path.exists()

    def test_index_summary_output(self, cli, sample_fasta):
        """Index command provides summary output."""
        result = cli("fasta", "index", str(sample_fasta))

        assert result.exit_code == 0
        # Should indicate files created
        assert len(result.stdout) > 0


class TestFastaStats:
    """Tests for: refget fasta stats <file>"""

    def test_outputs_stats_json(self, cli, sample_fasta):
        """Outputs statistics in JSON format."""
        result = cli("fasta", "stats", str(sample_fasta), "--json")

        data = assert_json_output(result, ["sequences", "total_length"])
        assert isinstance(data["sequences"], int)
        assert data["sequences"] > 0

    def test_stats_values(self, cli, sample_fasta):
        """Stats values are correct."""
        result = cli("fasta", "stats", str(sample_fasta), "--json")

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # sample_fasta has 2 sequences, each 8 bases
        assert data["sequences"] == 2
        assert data["total_length"] == 16

    def test_stats_plain_output(self, cli, sample_fasta):
        """Stats can output in plain text format."""
        result = cli("fasta", "stats", str(sample_fasta))

        assert result.exit_code == 0
        # Should have some output
        assert len(result.stdout.strip()) > 0

    def test_stats_known_file(self, cli):
        """Stats for known test file."""
        result = cli("fasta", "stats", str(BASE_FASTA), "--json")

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # base.fa: chrX(8), chr1(4), chr2(4) = 16 total
        assert data["sequences"] == 3
        assert data["total_length"] == 16


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

        # Should fail with non-zero exit code
        assert result.exit_code != 0


class TestFastaErrorHandling:
    """Test error handling for fasta commands."""

    def test_nonexistent_file(self, cli):
        """Graceful error for nonexistent file."""
        result = cli("fasta", "digest", "/path/to/nonexistent.fa")

        assert result.exit_code != 0
        # Should have informative error message
        assert len(result.stdout) > 0 or len(result.stderr if hasattr(result, 'stderr') else '') > 0

    def test_empty_fasta(self, cli, tmp_path):
        """Handle empty FASTA file."""
        empty = tmp_path / "empty.fa"
        empty.write_text("")

        result = cli("fasta", "stats", str(empty), "--json")

        # May succeed with 0 sequences or fail gracefully
        if result.exit_code == 0:
            data = json.loads(result.stdout)
            assert data["sequences"] == 0

    def test_permission_denied(self, cli, tmp_path):
        """Handle permission denied."""
        # This test may be skipped on systems where we can't change permissions
        protected = tmp_path / "protected.fa"
        protected.write_text(">chr1\nACGT\n")

        import os
        import stat
        try:
            os.chmod(protected, 0o000)
            result = cli("fasta", "digest", str(protected))
            assert result.exit_code != 0
        finally:
            os.chmod(protected, stat.S_IRUSR | stat.S_IWUSR)
