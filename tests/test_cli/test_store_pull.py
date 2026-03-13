# tests/test_cli/test_store_pull.py

"""Tests for refget store pull CLI command.

Note: The HTTP server fixtures use subprocess instead of threading because
gtars' open_remote (Rust/PyO3) holds the GIL during HTTP requests, which
would deadlock a Python-thread-based HTTP server.
"""

import importlib.util
import json
import os
import socket
import subprocess
import sys
import time

import pytest

_conftest_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conftest.py"
)
_spec = importlib.util.spec_from_file_location("tests_conftest", _conftest_path)
_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_conftest)

BASE_FASTA = _conftest.BASE_FASTA
DIFFERENT_NAMES_FASTA = _conftest.DIFFERENT_NAMES_FASTA

# Skip entire module if gtars is not installed
pytest.importorskip("gtars")


def _find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _start_http_server(directory: str, port: int) -> subprocess.Popen:
    """Start an HTTP server as a subprocess serving the given directory."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", directory],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for server to be ready
    max_wait = 5.0
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except (ConnectionRefusedError, OSError):
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError(f"HTTP server failed to start on port {port}")
    return proc


def _stop_http_server(proc: subprocess.Popen) -> None:
    """Stop an HTTP server subprocess."""
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture
def remote_store_server(cli, tmp_path):
    """Set up a local store, serve it over HTTP, yield (url, digest, source_store_path)."""
    source_store = tmp_path / "source_store"
    cli("store", "init", "--path", str(source_store))
    add_result = cli("store", "add", str(BASE_FASTA), "--path", str(source_store))
    assert add_result.exit_code == 0, f"Failed to add FASTA: {add_result.stdout}"
    digest = json.loads(add_result.stdout)["digest"]

    port = _find_free_port()
    proc = _start_http_server(str(source_store), port)

    yield f"http://127.0.0.1:{port}", digest, source_store

    _stop_http_server(proc)


@pytest.fixture
def multi_remote_store_server(cli, tmp_path):
    """Set up a local store with multiple FASTAs, serve over HTTP."""
    source_store = tmp_path / "multi_source_store"
    cli("store", "init", "--path", str(source_store))

    add_result1 = cli("store", "add", str(BASE_FASTA), "--path", str(source_store))
    assert add_result1.exit_code == 0
    digest1 = json.loads(add_result1.stdout)["digest"]

    add_result2 = cli("store", "add", str(DIFFERENT_NAMES_FASTA), "--path", str(source_store))
    assert add_result2.exit_code == 0
    digest2 = json.loads(add_result2.stdout)["digest"]

    port = _find_free_port()
    proc = _start_http_server(str(source_store), port)

    yield f"http://127.0.0.1:{port}", digest1, digest2, source_store

    _stop_http_server(proc)


@pytest.fixture
def local_store(cli, tmp_path):
    """Initialize an empty local store for pulling into."""
    store_path = tmp_path / "local_store"
    result = cli("store", "init", "--path", str(store_path))
    assert result.exit_code == 0
    return store_path


class TestStorePullBasic:
    """Core pull functionality tests."""

    def test_pull_single_digest(self, cli, tmp_path, remote_store_server):
        """Pull a known digest from the remote store server."""
        server_url, digest, _ = remote_store_server
        local_store = tmp_path / "pull_store"
        cli("store", "init", "--path", str(local_store))

        result = cli("store", "pull", digest, "--server", server_url, "--path", str(local_store))

        assert result.exit_code == 0, f"Pull failed: {result.stdout}"
        data = json.loads(result.stdout)
        assert data["status"] == "pulled"
        assert data["digest"] == digest

    def test_pull_creates_local_cache(self, cli, tmp_path, remote_store_server):
        """After pulling, the .remote_cache directory is created."""
        server_url, digest, _ = remote_store_server
        local_store = tmp_path / "cache_store"
        cli("store", "init", "--path", str(local_store))

        result = cli("store", "pull", digest, "--server", server_url, "--path", str(local_store))

        assert result.exit_code == 0
        cache_dir = local_store / ".remote_cache"
        assert cache_dir.exists()

    def test_pull_quiet_flag(self, cli, tmp_path, remote_store_server):
        """Pull with --quiet suppresses progress output."""
        server_url, digest, _ = remote_store_server
        local_store = tmp_path / "quiet_store"
        cli("store", "init", "--path", str(local_store))

        result = cli(
            "store", "pull", digest, "--server", server_url, "--path", str(local_store), "--quiet"
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "pulled"


class TestStorePullEager:
    """Eager sequence fetching tests."""

    def test_pull_eager_fetches_sequences(self, cli, tmp_path, remote_store_server):
        """Pull with --eager pre-fetches all sequences."""
        server_url, digest, _ = remote_store_server
        local_store = tmp_path / "eager_store"
        cli("store", "init", "--path", str(local_store))

        result = cli(
            "store", "pull", digest, "--server", server_url, "--path", str(local_store), "--eager"
        )

        assert result.exit_code == 0, f"Eager pull failed: {result.stdout}"
        data = json.loads(result.stdout)
        assert data["eager"] is True
        assert data["sequences_fetched"] > 0

    def test_pull_default_is_lazy(self, cli, tmp_path, remote_store_server):
        """Pull without --eager uses lazy mode."""
        server_url, digest, _ = remote_store_server
        local_store = tmp_path / "lazy_store"
        cli("store", "init", "--path", str(local_store))

        result = cli("store", "pull", digest, "--server", server_url, "--path", str(local_store))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["eager"] is False
        assert "sequences_fetched" not in data


class TestStorePullBatch:
    """Batch pull via --file tests."""

    def test_pull_from_file(self, cli, tmp_path, multi_remote_store_server):
        """Pull multiple digests from a file."""
        server_url, digest1, digest2, _ = multi_remote_store_server
        local_store = tmp_path / "batch_store"
        cli("store", "init", "--path", str(local_store))

        digest_file = tmp_path / "digests.txt"
        digest_file.write_text(f"{digest1}\n{digest2}\n")

        result = cli(
            "store",
            "pull",
            "--file",
            str(digest_file),
            "--server",
            server_url,
            "--path",
            str(local_store),
        )

        assert result.exit_code == 0, f"Batch pull failed: {result.stdout}"
        data = json.loads(result.stdout)
        assert "results" in data
        assert len(data["results"]) == 2

    def test_pull_file_with_blank_lines(self, cli, tmp_path, remote_store_server):
        """File with blank lines and whitespace is handled gracefully."""
        server_url, digest, _ = remote_store_server
        local_store = tmp_path / "blank_store"
        cli("store", "init", "--path", str(local_store))

        digest_file = tmp_path / "digests_blanks.txt"
        digest_file.write_text(f"\n  \n{digest}\n\n  \n")

        result = cli(
            "store",
            "pull",
            "--file",
            str(digest_file),
            "--server",
            server_url,
            "--path",
            str(local_store),
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Single digest after stripping blanks, so no "results" wrapper
        assert data["digest"] == digest
        assert data["status"] == "pulled"

    def test_pull_file_not_found(self, cli, tmp_path):
        """Passing a nonexistent file to --file returns error."""
        local_store = tmp_path / "nofile_store"
        cli("store", "init", "--path", str(local_store))

        result = cli(
            "store",
            "pull",
            "--file",
            "/nonexistent/digests.txt",
            "--server",
            "http://127.0.0.1:1",
            "--path",
            str(local_store),
        )

        assert result.exit_code != 0

    def test_pull_empty_file(self, cli, tmp_path, remote_store_server):
        """Empty file returns error about no digests."""
        server_url, _, _ = remote_store_server
        local_store = tmp_path / "empty_file_store"
        cli("store", "init", "--path", str(local_store))

        digest_file = tmp_path / "empty.txt"
        digest_file.write_text("")

        result = cli(
            "store",
            "pull",
            "--file",
            str(digest_file),
            "--server",
            server_url,
            "--path",
            str(local_store),
        )

        assert result.exit_code != 0


class TestStorePullAlreadyLocal:
    """Skip already-cached collections."""

    def test_pull_already_local(self, cli, tmp_path, remote_store_server):
        """Pulling a digest that exists locally returns already_local status."""
        server_url, digest, _ = remote_store_server
        local_store = tmp_path / "already_store"
        cli("store", "init", "--path", str(local_store))

        # Add the same FASTA to local store
        cli("store", "add", str(BASE_FASTA), "--path", str(local_store))

        # Try to pull -- should detect it is already local
        result = cli("store", "pull", digest, "--server", server_url, "--path", str(local_store))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "already_local"


class TestStorePullErrors:
    """Error case tests."""

    def test_pull_nonexistent_digest(self, cli, tmp_path, remote_store_server):
        """Pull a digest that does not exist on the remote."""
        server_url, _, _ = remote_store_server
        local_store = tmp_path / "nonexist_store"
        cli("store", "init", "--path", str(local_store))

        result = cli(
            "store",
            "pull",
            "NONEXISTENT_DIGEST_12345678901234",
            "--server",
            server_url,
            "--path",
            str(local_store),
        )

        assert result.exit_code != 0
        data = json.loads(result.stdout)
        assert data["status"] == "not_found"

    def test_pull_unreachable_server(self, cli, tmp_path):
        """Pull from an unreachable URL returns error."""
        local_store = tmp_path / "unreach_store"
        cli("store", "init", "--path", str(local_store))

        result = cli(
            "store",
            "pull",
            "some_digest_abc123",
            "--server",
            "http://127.0.0.1:1",
            "--path",
            str(local_store),
        )

        assert result.exit_code != 0

    def test_pull_no_digest_or_file(self, cli, tmp_path):
        """Pull with neither digest nor --file returns error."""
        local_store = tmp_path / "noarg_store"
        cli("store", "init", "--path", str(local_store))

        result = cli("store", "pull", "--server", "http://127.0.0.1:1", "--path", str(local_store))

        assert result.exit_code != 0

    def test_pull_both_digest_and_file(self, cli, tmp_path):
        """Pull with both digest and --file returns error."""
        local_store = tmp_path / "both_store"
        cli("store", "init", "--path", str(local_store))

        digest_file = tmp_path / "digests.txt"
        digest_file.write_text("some_digest\n")

        result = cli(
            "store",
            "pull",
            "some_digest",
            "--file",
            str(digest_file),
            "--server",
            "http://127.0.0.1:1",
            "--path",
            str(local_store),
        )

        assert result.exit_code != 0

    def test_pull_no_server_configured(self, cli, tmp_path, monkeypatch):
        """Pull without --server and no configured remotes returns error."""
        local_store = tmp_path / "noserver_store"
        cli("store", "init", "--path", str(local_store))

        # Patch _find_remote_urls to return empty list
        monkeypatch.setattr("refget.cli.store._find_remote_urls", lambda server_override=None: [])

        result = cli("store", "pull", "some_digest", "--path", str(local_store))

        assert result.exit_code != 0


class TestStorePullMultipleRemotes:
    """Fallback across multiple remotes."""

    def test_pull_tries_next_remote_on_failure(
        self, cli, tmp_path, remote_store_server, monkeypatch
    ):
        """When first remote lacks the digest, tries the next one."""
        server_url, digest, _ = remote_store_server

        # Set up an empty store served over HTTP (first remote)
        empty_store = tmp_path / "empty_remote"
        cli("store", "init", "--path", str(empty_store))

        port = _find_free_port()
        empty_proc = _start_http_server(str(empty_store), port)
        empty_url = f"http://127.0.0.1:{port}"

        try:
            local_store = tmp_path / "multi_remote_store"
            cli("store", "init", "--path", str(local_store))

            # Patch to return empty server first, then the populated one
            monkeypatch.setattr(
                "refget.cli.store._find_remote_urls",
                lambda server_override=None: [empty_url, server_url],
            )

            result = cli("store", "pull", digest, "--path", str(local_store), "--quiet")

            assert result.exit_code == 0, f"Multi-remote pull failed: {result.stdout}"
            # Extract JSON from output (error messages from failed remotes may precede it)
            stdout = result.stdout
            json_start = stdout.rfind("{")
            assert json_start >= 0, f"No JSON found in output: {stdout}"
            data = json.loads(stdout[json_start:])
            assert data["status"] == "pulled"
            assert data["source"] == server_url
        finally:
            _stop_http_server(empty_proc)
