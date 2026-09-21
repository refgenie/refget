# tests/test_cli/test_store_pull.py

"""Tests for refget store pull CLI command.

Note: The HTTP server fixtures use subprocess instead of threading because
gtars' open_remote (Rust/PyO3) holds the GIL during HTTP requests, which
would deadlock a Python-thread-based HTTP server.
"""

import hashlib
import json
import socket
import subprocess
import sys
import time

import pytest

from tests._test_data import BASE_FASTA, DIFFERENT_NAMES_FASTA

# Skip entire module if gtars is not installed
pytest.importorskip("gtars")


def _find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _start_http_server(
    directory: str, port: int, *, range_support: bool = False
) -> subprocess.Popen:
    """Start a subprocess HTTP server serving a store directory."""
    if range_support:
        command = [
            sys.executable,
            "-c",
            (
                "import sys; from http.server import ThreadingHTTPServer; "
                "from refget.cli._explore_server import make_explore_handler; "
                "ThreadingHTTPServer(('127.0.0.1', int(sys.argv[2])), "
                "make_explore_handler(sys.argv[1], None)).serve_forever()"
            ),
            directory,
            str(port),
        ]
    else:
        command = [sys.executable, "-m", "http.server", str(port), "--directory", directory]
    proc = subprocess.Popen(
        command,
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


def _add_text_collection(cli, store_path, fasta_path, contents):
    fasta_path.write_text(contents)
    result = cli("store", "add", str(fasta_path), "--path", str(store_path))
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)["digest"]


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
        """After pulling, a per-origin cache with an origin marker is created."""
        server_url, digest, _ = remote_store_server
        local_store = tmp_path / "cache_store"
        cli("store", "init", "--path", str(local_store))

        result = cli("store", "pull", digest, "--server", server_url, "--path", str(local_store))

        assert result.exit_code == 0
        cache_dir = local_store / ".remote_cache"
        assert cache_dir.exists()
        origin_caches = [path for path in cache_dir.iterdir() if path.is_dir()]
        assert len(origin_caches) == 1
        assert len(origin_caches[0].name) == 16
        assert (origin_caches[0] / ".origin").read_text().strip() == server_url

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


class TestStorePullMaterializes:
    """Pull materializes collections (sequences + aliases + FHR) into the local store."""

    def test_pull_persists_collection_locally(self, cli, tmp_path, remote_store_server):
        """After pulling, the collection is present in the local store (materialized)."""
        server_url, digest, _ = remote_store_server
        local_store = tmp_path / "materialized_store"
        cli("store", "init", "--path", str(local_store))

        result = cli("store", "pull", digest, "--server", server_url, "--path", str(local_store))
        assert result.exit_code == 0, f"Pull failed: {result.stdout}"

        # The collection should now be listed in the local store.
        list_result = cli("store", "list", "--path", str(local_store))
        assert list_result.exit_code == 0
        collections = [c["digest"] for c in json.loads(list_result.stdout)["collections"]]
        assert digest in collections

    def test_pull_transfers_aliases_and_fhr(self, cli, tmp_path):
        """import_collection carries the collection's aliases and FHR metadata."""
        # Build a source store with an alias and FHR on the collection.
        source_store = tmp_path / "alias_source"
        cli("store", "init", "--path", str(source_store))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(source_store))
        assert add_result.exit_code == 0
        digest = json.loads(add_result.stdout)["digest"]

        cli("store", "alias", "add", "test", "mygenome", digest, "--path", str(source_store))
        cli("store", "fhr", "set-fields", digest, "--genome", "myorg", "--path", str(source_store))

        port = _find_free_port()
        proc = _start_http_server(str(source_store), port)
        try:
            server_url = f"http://127.0.0.1:{port}"
            local_store = tmp_path / "alias_dest"
            cli("store", "init", "--path", str(local_store))

            result = cli(
                "store", "pull", digest, "--server", server_url, "--path", str(local_store)
            )
            assert result.exit_code == 0, f"Pull failed: {result.stdout}"

            # Alias should have travelled with the collection.
            alias_result = cli("store", "alias", "for", digest, "--path", str(local_store))
            assert alias_result.exit_code == 0
            aliases = json.loads(alias_result.stdout)["aliases"]
            assert ["test", "mygenome"] in aliases

            # FHR should have travelled too.
            fhr_result = cli("store", "fhr", "get", digest, "--path", str(local_store))
            assert fhr_result.exit_code == 0
            assert "myorg" in fhr_result.stdout
        finally:
            _stop_http_server(proc)


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
            json_start = stdout.find("{")
            assert json_start >= 0, f"No JSON found in output: {stdout}"
            data = json.loads(stdout[json_start:])
            assert data["status"] == "pulled"
            assert data["source"] == server_url
        finally:
            _stop_http_server(empty_proc)


class TestRemoteStoreIntegrity:
    """Broad remote cache, refresh, and alias integrity scenarios."""

    def test_lazy_remote_reads_cache_only_the_requested_sequence(self, cli, tmp_path):
        """Inventory and ranges stay metadata-only; whole reads cache one body."""
        from refget.cli.store import _remote_cache_dir

        source = tmp_path / "lazy_source"
        assert cli("store", "init", "--path", str(source)).exit_code == 0
        digest = _add_text_collection(
            cli, source, tmp_path / "lazy.fa", ">chr1\nACGTACGT\n>chr2\nTTAA\n"
        )
        local_listing = cli("store", "list", digest, "--path", str(source))
        sequence_digest = json.loads(local_listing.stdout)["sequences"][0]["digest"]

        port = _find_free_port()
        proc = _start_http_server(str(source), port, range_support=True)
        try:
            remote_url = f"http://127.0.0.1:{port}"
            client = tmp_path / "lazy_client"
            cache_dir = _remote_cache_dir(client, remote_url)

            inventory = cli(
                "store", "list", "--sequences", "--path", str(client), "--remote", remote_url
            )
            assert inventory.exit_code == 0, inventory.output
            assert len(json.loads(inventory.stdout)["sequences"]) == 2
            assert list(cache_dir.rglob("*.seq")) == []

            substring = cli(
                "store", "get", sequence_digest, "--sequence", "--start", "0", "--end", "3",
                "--path", str(client), "--remote", remote_url,
            )
            assert substring.exit_code == 0, substring.output
            assert substring.stdout.strip() == "ACG"
            assert list(cache_dir.rglob("*.seq")) == []

            bed = tmp_path / "lazy.bed"
            bed.write_text("chr2\t0\t2\n")
            regions = cli(
                "store", "regions", digest, "--bed", str(bed), "--json",
                "--path", str(client), "--remote", remote_url,
            )
            assert regions.exit_code == 0, regions.output
            assert json.loads(regions.stdout)[0]["sequence"] == "TT"
            assert list(cache_dir.rglob("*.seq")) == []

            whole = cli(
                "store", "get", sequence_digest, "--sequence",
                "--path", str(client), "--remote", remote_url,
            )
            assert whole.exit_code == 0, whole.output
            assert whole.stdout.strip() == "ACGTACGT"
            assert len(list(cache_dir.rglob("*.seq"))) == 1
        finally:
            _stop_http_server(proc)

    def test_origin_isolation_alias_resolution_and_shared_cache_guard(self, cli, tmp_path):
        from gtars.refget import RefgetStore
        from refget.cli.store import _normalize_remote_url

        remote_root = tmp_path / "remotes"
        store_a = remote_root / "a"
        store_b = remote_root / "b"
        assert cli("store", "init", "--path", str(store_a)).exit_code == 0
        assert cli("store", "init", "--path", str(store_b)).exit_code == 0

        digest_a = _add_text_collection(
            cli, store_a, tmp_path / "a1.fa", ">chr1\nACGT\n>chr2\nGGCC\n"
        )
        digest_a_peer = _add_text_collection(
            cli, store_a, tmp_path / "a2.fa", ">one\nACGT\n>extra\nTTAA\n"
        )
        digest_b = _add_text_collection(
            cli, store_b, tmp_path / "b.fa", ">other\nCCCC\n"
        )
        alias = cli(
            "store", "alias", "add", "ucsc", "assembly-a", digest_a,
            "--path", str(store_a),
        )
        assert alias.exit_code == 0, alias.output

        port = _find_free_port()
        proc = _start_http_server(str(remote_root), port)
        try:
            url_a = f"http://127.0.0.1:{port}/a/"
            url_b = f"HTTP://127.0.0.1:{port}/b#ignored"
            normalized_a = _normalize_remote_url(url_a)
            normalized_b = _normalize_remote_url(url_b)
            client_store = tmp_path / "client"

            list_a = cli(
                "store", "list", "--path", str(client_store), "--remote", url_a
            )
            list_b = cli(
                "store", "list", "--path", str(client_store), "--remote", url_b
            )
            assert list_a.exit_code == 0, list_a.output
            assert list_b.exit_code == 0, list_b.output
            collections_a = json.loads(list_a.stdout)["collections"]
            collections_b = json.loads(list_b.stdout)["collections"]
            assert {row["digest"] for row in collections_a} == {digest_a, digest_a_peer}
            assert {row["digest"] for row in collections_b} == {digest_b}
            assert next(row for row in collections_a if row["digest"] == digest_a)["aliases"] == [
                ["ucsc", "assembly-a"]
            ]

            match = cli(
                "store", "match", "ucsc:assembly-a", digest_a_peer,
                "--path", str(client_store), "--remote", url_a,
            )
            assert match.exit_code == 0, match.output
            assert json.loads(match.stdout)["matches"][0]["names_a"] == ["chr1"]

            cache_root = client_store / ".remote_cache"
            cache_dirs = sorted(path for path in cache_root.iterdir() if path.is_dir())
            assert len(cache_dirs) == 2
            assert all(len(path.name) == 16 for path in cache_dirs)
            assert {path.name for path in cache_dirs} == {
                hashlib.sha256(normalized_a.encode()).hexdigest()[:16],
                hashlib.sha256(normalized_b.encode()).hexdigest()[:16],
            }
            assert {(path / ".origin").read_text().strip() for path in cache_dirs} == {
                normalized_a,
                normalized_b,
            }

            shared_cache = tmp_path / "deliberately_shared_cache"
            RefgetStore.open_remote(str(shared_cache), normalized_a)
            with pytest.raises(OSError) as error:
                RefgetStore.open_remote(str(shared_cache), normalized_b)
            assert normalized_a in str(error.value)
            assert normalized_b in str(error.value)
        finally:
            _stop_http_server(proc)

    def test_manifest_refresh_preserves_payload_and_rejects_missing_alias(self, cli, tmp_path):
        from refget.cli.store import _remote_cache_dir

        remote_root = tmp_path / "refresh_remote"
        source_store = remote_root / "store"
        assert cli("store", "init", "--path", str(source_store)).exit_code == 0
        digest = _add_text_collection(
            cli, source_store, tmp_path / "initial.fa", ">chr1\nACGTACGT\n"
        )
        local_collection = cli("store", "list", digest, "--path", str(source_store))
        assert local_collection.exit_code == 0, local_collection.output
        sequence_digest = json.loads(local_collection.stdout)["sequences"][0]["digest"]

        port = _find_free_port()
        proc = _start_http_server(str(remote_root), port)
        try:
            remote_url = f"http://127.0.0.1:{port}/store"
            client_store = tmp_path / "refresh_client"
            prime = cli(
                "store", "get", sequence_digest, "--sequence",
                "--path", str(client_store), "--remote", remote_url,
            )
            assert prime.exit_code == 0, prime.output

            cache_dir = _remote_cache_dir(client_store, remote_url)
            payloads = list(cache_dir.rglob("*.seq"))
            assert payloads
            preserved_payload = payloads[0]
            preserved_bytes = preserved_payload.read_bytes()

            alias = cli(
                "store", "alias", "add", "ucsc", "refreshed", digest,
                "--path", str(source_store),
            )
            assert alias.exit_code == 0, alias.output
            new_digest = _add_text_collection(
                cli, source_store, tmp_path / "new.fa", ">new\nTTAA\n"
            )

            refreshed = cli(
                "store", "list", "--path", str(client_store), "--remote", remote_url
            )
            assert refreshed.exit_code == 0, refreshed.output
            collections = json.loads(refreshed.stdout)["collections"]
            assert {row["digest"] for row in collections} == {digest, new_digest}
            assert next(row for row in collections if row["digest"] == digest)["aliases"] == [
                ["ucsc", "refreshed"]
            ]
            assert preserved_payload.exists()
            assert preserved_payload.read_bytes() == preserved_bytes

            manifest_path = source_store / "rgstore.json"
            manifest = json.loads(manifest_path.read_text())
            manifest.setdefault("collection_alias_namespaces", []).append("missing-ns")
            manifest["aliases_digest"] = "deliberately-missing-alias-sidecar"
            manifest_path.write_text(json.dumps(manifest, indent=2))

            corrupt = cli(
                "store", "list", "--path", str(client_store), "--remote", remote_url
            )
            assert corrupt.exit_code != 0
            assert "missing-ns" in corrupt.output
            assert remote_url in corrupt.output
        finally:
            _stop_http_server(proc)
