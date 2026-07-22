"""
Single-origin static file server for ``refget store explore``.

Serves a RefgetStore's raw files under ``/store/`` and the bundled Store
Explorer SPA at ``/`` from one localhost origin. Because both live on the same
origin, the browser's ``fetch()`` calls are same-origin and need no CORS.

The handler is read-only: only ``GET`` and ``HEAD`` are allowed (matching the
read-only CVMFS/S3 sources this command targets). HTTP ``Range`` requests are
supported so the Explorer can load a bounded prefix of large index files
(``sequences.rgsi``) instead of downloading them whole — the stdlib
``SimpleHTTPRequestHandler`` does not implement Range, so we add it here.
"""

import os
from http.server import SimpleHTTPRequestHandler

_STORE_PREFIX = "/store"
_CHUNK = 64 * 1024


class ExploreHandler(SimpleHTTPRequestHandler):
    """Route ``/store/*`` to the store dir and everything else to the SPA dir.

    ``store_dir`` and ``spa_dir`` are set on a subclass by
    :func:`make_explore_handler`. When ``spa_dir`` is ``None`` (``--store-only``
    mode), the store is served at the root instead of under ``/store/``.
    """

    store_dir = None
    spa_dir = None

    # --- routing -----------------------------------------------------------

    def _route(self, path):
        """Map a request path to ``(root_dir, effective_path)``."""
        clean = path.split("?", 1)[0].split("#", 1)[0]
        under_store = clean == _STORE_PREFIX or clean.startswith(_STORE_PREFIX + "/")
        if self.spa_dir is None:
            # store-only: serve the store at both / and /store/
            if under_store:
                return self.store_dir, (path[len(_STORE_PREFIX) :] or "/")
            return self.store_dir, path
        if under_store:
            return self.store_dir, (path[len(_STORE_PREFIX) :] or "/")
        return self.spa_dir, path

    def translate_path(self, path):
        root, effective = self._route(path)
        # SimpleHTTPRequestHandler.translate_path resolves relative to
        # self.directory and already blocks ".." traversal; we just point it at
        # the correct root per request (handler instances are per-connection).
        self.directory = root
        return super().translate_path(effective)

    def send_head(self):
        clean = self.path.split("?", 1)[0].split("#", 1)[0]
        under_store = clean == _STORE_PREFIX or clean.startswith(_STORE_PREFIX + "/")
        # SPA client-side routes (e.g. /explore-store/overview) are not real
        # files; serve index.html so React Router can handle them. Restrict the
        # fallback to extension-less paths so a genuinely missing asset (e.g.
        # /assets/foo.js) still returns 404.
        if (
            self.spa_dir is not None
            and not under_store
            and "." not in clean.rsplit("/", 1)[-1]
            and not os.path.exists(self.translate_path(self.path))
        ):
            self.path = "/index.html"

        # Honor a single-range Range request; fall through to a normal 200 for
        # anything we don't handle (no header, multi-range, directory, missing).
        if "Range" in self.headers and self._send_range():
            return None
        return super().send_head()

    # --- Range support -----------------------------------------------------

    @staticmethod
    def _parse_range(header, size):
        """Parse a single ``bytes=`` Range header into inclusive (start, end).

        Returns None for anything unsupported (non-bytes unit, multi-range,
        malformed) so the caller serves the full file instead.
        """
        if not header.startswith("bytes="):
            return None
        spec = header[len("bytes=") :].strip()
        if "," in spec:
            return None  # multi-range not supported
        start_s, sep, end_s = spec.partition("-")
        if sep == "":
            return None
        try:
            if start_s == "":
                # Suffix range: final N bytes.
                n = int(end_s)
                if n <= 0:
                    return None
                start, end = max(0, size - n), size - 1
            else:
                start = int(start_s)
                end = int(end_s) if end_s != "" else size - 1
        except ValueError:
            return None
        return start, min(end, size - 1)

    def _send_range(self):
        """Serve a partial 206 response. Return True if fully handled."""
        path = self.translate_path(self.path)
        if os.path.isdir(path) or not os.path.exists(path):
            return False
        try:
            f = open(path, "rb")
        except OSError:
            return False
        try:
            fs = os.fstat(f.fileno())
            size = fs.st_size
            parsed = self._parse_range(self.headers["Range"], size)
            if parsed is None:
                return False  # serve full file
            start, end = parsed
            if start >= size or start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return True
            length = end - start + 1
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            if self.command == "GET":
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(_CHUNK, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            return True
        finally:
            f.close()

    # --- read-only enforcement --------------------------------------------

    def _reject(self):
        self.send_error(405, "Method Not Allowed")

    do_POST = _reject
    do_PUT = _reject
    do_DELETE = _reject
    do_PATCH = _reject


def make_explore_handler(store_dir, spa_dir):
    """Build an :class:`ExploreHandler` subclass bound to the given dirs.

    Args:
        store_dir: Filesystem path to the RefgetStore directory.
        spa_dir: Filesystem path to the Store Explorer SPA build, or ``None``
            for store-only mode.
    """
    return type(
        "BoundExploreHandler",
        (ExploreHandler,),
        {"store_dir": str(store_dir), "spa_dir": str(spa_dir) if spa_dir else None},
    )
