"""Tests for `refget store explore` — the single-origin static server."""

import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from refget.cli._explore_server import make_explore_handler
from refget.cli.store import _find_spa_dir, _looks_like_spa


@pytest.fixture
def spa_dir(tmp_path):
    """A minimal directory that looks like a built Store Explorer SPA."""
    d = tmp_path / "dist"
    d.mkdir()
    (d / "index.html").write_text('<html><body><div id="root"></div></body></html>')
    (d / "assets").mkdir()
    (d / "assets" / "app.js").write_text("console.log('spa');")
    return d


def _serve(store_path, spa_path):
    """Start an explore server on an ephemeral port; return (base_url, stop)."""
    handler = make_explore_handler(store_path, spa_path)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"

    def stop():
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)

    return base, stop


def _request(url, method="GET", headers=None):
    """Return (status, body_bytes, headers) — treating HTTP errors as responses."""
    req = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


# ============================================================
# _looks_like_spa / _find_spa_dir helpers
# ============================================================


def test_looks_like_spa_true(spa_dir):
    assert _looks_like_spa(spa_dir) is True


def test_looks_like_spa_false_for_non_spa(tmp_path):
    (tmp_path / "index.html").write_text("<html><body>Just an API landing page</body></html>")
    assert _looks_like_spa(tmp_path) is False


def test_looks_like_spa_false_when_missing(tmp_path):
    assert _looks_like_spa(tmp_path / "nope") is False


def test_find_spa_dir_explicit_override(spa_dir):
    assert _find_spa_dir(spa_dir) == spa_dir.resolve()


def test_find_spa_dir_explicit_missing_index_errors(tmp_path):
    import typer

    with pytest.raises(typer.Exit):
        _find_spa_dir(tmp_path)  # no index.html


# ============================================================
# Serving behavior (against a real populated store)
# ============================================================


def test_serves_store_files_under_prefix(populated_store, spa_dir):
    base, stop = _serve(populated_store["path"], spa_dir)
    try:
        status, body, _ = _request(f"{base}/store/rgstore.json")
        assert status == 200
        assert b'"version"' in body
    finally:
        stop()


def test_serves_spa_at_root(populated_store, spa_dir):
    base, stop = _serve(populated_store["path"], spa_dir)
    try:
        status, body, _ = _request(f"{base}/")
        assert status == 200
        assert b'id="root"' in body
    finally:
        stop()


def test_spa_client_route_falls_back_to_index(populated_store, spa_dir):
    base, stop = _serve(populated_store["path"], spa_dir)
    try:
        status, body, _ = _request(f"{base}/explore-store/overview?url=/store/")
        assert status == 200
        assert b'id="root"' in body
    finally:
        stop()


def test_missing_asset_is_404(populated_store, spa_dir):
    base, stop = _serve(populated_store["path"], spa_dir)
    try:
        status, _, _ = _request(f"{base}/assets/does-not-exist.js")
        assert status == 404
    finally:
        stop()


def test_range_request_returns_206(populated_store, spa_dir):
    base, stop = _serve(populated_store["path"], spa_dir)
    try:
        status, body, headers = _request(
            f"{base}/store/collections.rgci", headers={"Range": "bytes=0-9"}
        )
        assert status == 206
        assert len(body) == 10
        assert headers["Content-Range"].startswith("bytes 0-9/")
    finally:
        stop()


def test_suffix_range_request(populated_store, spa_dir):
    base, stop = _serve(populated_store["path"], spa_dir)
    try:
        status, body, _ = _request(f"{base}/store/collections.rgci", headers={"Range": "bytes=-8"})
        assert status == 206
        assert len(body) == 8
    finally:
        stop()


def test_unsatisfiable_range_returns_416(populated_store, spa_dir):
    base, stop = _serve(populated_store["path"], spa_dir)
    try:
        status, _, _ = _request(f"{base}/store/rgstore.json", headers={"Range": "bytes=99999999-"})
        assert status == 416
    finally:
        stop()


def test_post_is_rejected_405(populated_store, spa_dir):
    base, stop = _serve(populated_store["path"], spa_dir)
    try:
        status, _, _ = _request(f"{base}/store/rgstore.json", method="POST")
        assert status == 405
    finally:
        stop()


def test_store_only_serves_files_at_root(populated_store):
    base, stop = _serve(populated_store["path"], None)
    try:
        # Store served at root...
        status_root, body, _ = _request(f"{base}/rgstore.json")
        assert status_root == 200
        assert b'"version"' in body
        # ...and also under /store/ for URL compatibility.
        status_prefixed, _, _ = _request(f"{base}/store/rgstore.json")
        assert status_prefixed == 200
    finally:
        stop()
