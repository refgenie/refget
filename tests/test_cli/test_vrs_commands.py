# tests/test_cli/test_vrs_commands.py

"""Tests for refget vrs CLI commands."""

import importlib.util
import json
import os

import pytest

_conftest_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conftest.py"
)
_spec = importlib.util.spec_from_file_location("tests_conftest", _conftest_path)
_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_conftest)

BASE_FASTA = _conftest.BASE_FASTA

pytest.importorskip("gtars")


VCF_CONTENT = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chrX\t1\t.\tT\tA\t.\t.\t.
chr1\t1\t.\tG\tC\t.\t.\t.
"""


def _setup_store(cli, tmp_path):
    store_path = tmp_path / "store"
    cli("store", "init", "--path", str(store_path))
    add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
    digest = json.loads(add_result.stdout)["digest"]
    vcf = tmp_path / "variants.vcf"
    vcf.write_text(VCF_CONTENT)
    return store_path, digest, vcf


class TestVrsCompute:
    """Tests for: refget vrs compute <digest> <vcf>"""

    def test_compute_tsv(self, cli, tmp_path):
        """Default output is tab-separated VRS records."""
        store_path, digest, vcf = _setup_store(cli, tmp_path)
        result = cli("vrs", "compute", digest, str(vcf), "--path", str(store_path))
        assert result.exit_code == 0, result.stdout
        lines = [ln for ln in result.stdout.strip().splitlines() if ln.strip()]
        assert len(lines) == 2
        # Each line: chrom, pos, ref, alt, vrs_id
        for ln in lines:
            fields = ln.split("\t")
            assert len(fields) == 5
            assert fields[4].startswith("ga4gh:VA.")

    def test_compute_json(self, cli, tmp_path):
        """--json emits a list of VRS dicts."""
        store_path, digest, vcf = _setup_store(cli, tmp_path)
        result = cli(
            "vrs", "compute", digest, str(vcf), "--json", "--path", str(store_path)
        )
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 2
        for rec in data:
            assert set(rec) == {"chrom", "pos", "ref", "alt", "vrs_id"}
            assert rec["vrs_id"].startswith("ga4gh:VA.")

    def test_compute_output_file(self, cli, tmp_path):
        """--output writes JSON results to a file."""
        store_path, digest, vcf = _setup_store(cli, tmp_path)
        out = tmp_path / "vrs.json"
        result = cli(
            "vrs", "compute", digest, str(vcf), "-o", str(out), "--path", str(store_path)
        )
        assert result.exit_code == 0, result.stdout
        assert out.exists()
        data = json.loads(out.read_text())
        assert len(data) == 2
