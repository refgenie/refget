"""Tests for: refget blast, a pass-through to gtars blast (gtars' own tests cover the verbs)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from refget.cli.blast import store_argv
from tests._test_data import BASE_FASTA, DIFFERENT_NAMES_FASTA

BLAST_DATA = Path(__file__).resolve().parents[1] / "data" / "blast"

blast = pytest.importorskip("gtars.blast")


def _run_cli(*args):
    """Run the CLI in a subprocess: gtars writes straight to file descriptors 1 and 2."""
    cmd = [sys.executable, "-m", "refget.cli.main", *args]
    return subprocess.run(cmd, capture_output=True, text=True)


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GTARS_RGBLAST_CACHE", str(tmp_path / "nstats-cache"))
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")


@pytest.fixture
def store(cli, tmp_path):
    """A store with base.fa (ucsc:hg38), different_names.fa (ucsc:other) and a collection of its own."""
    store_path = tmp_path / "store"
    cli("store", "init", "--path", str(store_path))
    uniq = tmp_path / "uniq.fa"
    uniq.write_text(">u1\nACGTACGTACGTTTGACCA\n>u2\nCCCGGGATATATTT\n")
    digests = {}
    for name, fasta in [("base", BASE_FASTA), ("other", DIFFERENT_NAMES_FASTA), ("uniq", uniq)]:
        added = cli("store", "add", str(fasta), "--path", str(store_path))
        digests[name] = json.loads(added.stdout)["digest"]
    cli("store", "alias", "add", "ucsc", "hg38", digests["base"], "--path", str(store_path))
    cli("store", "alias", "add", "ucsc", "other", digests["other"], "--path", str(store_path))
    return store_path, digests


def _files(prefix):
    return sorted(p for p in prefix.parent.iterdir() if p.name.startswith(prefix.name))


def test_store_argv_maps_path_and_remote_to_store(tmp_path, monkeypatch):
    p = str(tmp_path / "s")
    assert store_argv(["build", "-p", p, "--all"]) == ["build", "--store", p, "--all"]
    assert store_argv(["build", f"--path={p}", "--all"]) == ["build", "--store", p, "--all"]
    url = "https://example.org/store"
    assert store_argv(["verify", "-p", p, "-r", url]) == ["verify", "--store", url]
    assert store_argv(["build", "--store", "x", "--all"]) == ["build", "--store", "x", "--all"]
    assert store_argv(["build", "--help"]) == ["build", "--help"]
    # engine arguments after -- are left alone; verbs without a store are unchanged
    assert store_argv(["search", "-p", p, "--", "-p", "1"]) == ["search", "--store", p, "--", "-p", "1"]
    assert store_argv(["report", "hits.tsv", "-p", p]) == ["report", "hits.tsv", "-p", p]
    assert store_argv([]) == []
    # no -p/-r: the configured store
    monkeypatch.setattr("refget.cli.blast._get_store_path", lambda path: Path("/configured"))
    assert store_argv(["nstats", "--all"]) == ["nstats", "--store", "/configured", "--all"]
    # --engine blastn searches --db and gets no store
    a = ["search", "--engine", "blastn", "--db", "d", "--", "-query", "q.fa"]
    assert store_argv(a) == a
    assert store_argv(["search", "--all", "--", "--db", "x"])[:3] == ["search", "--store", "/configured"]


def test_blast_listed_in_help_and_passes_help_through(cli):
    assert "blast" in cli("--help").stdout
    proc = _run_cli("blast", "--help")
    assert proc.returncode == 0, proc.stderr
    for verb in ("build", "verify", "view", "nstats", "search", "report", "origin", "reps"):
        assert verb in proc.stdout


def test_build_verify_through_the_pass_through(cli, store, tmp_path):
    store_path, _ = store
    out = tmp_path / "db" / "x"
    out.parent.mkdir()
    proc = _run_cli("blast", "build", "-p", str(store_path), "--collection", "ucsc:hg38", "--out", str(out), "-q")
    assert proc.returncode == 0, proc.stderr
    assert _files(out)
    proc = _run_cli("blast", "verify", "--db", str(out), "-p", str(store_path))
    assert proc.returncode == 0 and "OK" in proc.stderr
    # a usage error exits 2 with clap's message
    proc = _run_cli("blast", "build", "-p", str(store_path), "--out", str(out))
    assert proc.returncode == 2 and "error" in proc.stderr


def test_report_tsv_matches_the_fixture():
    proc = _run_cli(
        "blast", "report", str(BLAST_DATA / "small_jungle_hits.tsv"), "--db", str(BLAST_DATA / "small_jungle"),
        "--query", str(BLAST_DATA / "small_jungle_queries.fa"),
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == (BLAST_DATA / "expected_summary.tsv").read_text()


def _dna_store(cli, tmp_path):
    """Two collections of random 2 kb sequences (they share one) and a query cut from the first."""
    import random

    rng = random.Random(7)
    seqs = ["".join(rng.choice("ACGT") for _ in range(2000)) for _ in range(3)]
    store_path = tmp_path / "dnastore"
    cli("store", "init", "--path", str(store_path))
    for i, recs in enumerate([seqs[:2], seqs[1:]]):
        fa = tmp_path / f"c{i}.fa"
        fa.write_text("".join(f">s{i}_{j}\n{x}\n" for j, x in enumerate(recs)))
        digest = json.loads(cli("store", "add", str(fa), "--path", str(store_path)).stdout)["digest"]
        cli("store", "alias", "add", "ucsc", f"c{i}", digest, "--path", str(store_path))
    q = tmp_path / "q.fa"
    q.write_text(">q1\n" + seqs[0][500:900] + "\n")
    return store_path, q


def test_rgblastn_search(cli, tmp_path):
    store_path, q = _dna_store(cli, tmp_path)
    proc = _run_cli(
        "blast", "search", "-p", str(store_path), "--all",
        "--", "-query", str(q), "-outfmt", "6",
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.startswith("q1\t")
