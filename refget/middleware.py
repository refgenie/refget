"""
Middleware for store-backed seqcolapi deployments.

StoreFreshnessMiddleware periodically checks if the remote store has changed
(via rgstore.json digest) and reloads the backend when new data is available.
"""

import json
import logging
import time
import urllib.request

from starlette.middleware.base import BaseHTTPMiddleware

_LOGGER = logging.getLogger(__name__)


class StoreFreshnessMiddleware(BaseHTTPMiddleware):
    """On each request, if >N seconds since last check, fetch rgstore.json
    and compare collections_digest. If changed, re-open the store and
    swap the backend. Lazy, request-triggered, no background threads."""

    def __init__(self, app, store_url: str, cache_dir: str, check_interval: int = 300):
        super().__init__(app)
        self.store_url = store_url
        self.cache_dir = cache_dir
        self.check_interval = check_interval
        self.last_check = time.time()
        self.last_digest = None

    async def dispatch(self, request, call_next):
        now = time.time()
        if now - self.last_check > self.check_interval:
            self.last_check = now
            self._check_and_reload(request.app)
        return await call_next(request)

    def _check_and_reload(self, app):
        try:
            metadata = self._fetch_metadata()
            digest = metadata.get("collections_digest")
            if digest and digest != self.last_digest:
                self.last_digest = digest
                self._reload_backend(app)
        except Exception as e:
            _LOGGER.warning(f"Store freshness check failed: {e}")

    def _fetch_metadata(self) -> dict:
        url = self.store_url.rstrip("/") + "/rgstore.json"
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read())

    def _reload_backend(self, app):
        from refget.backend import RefgetStoreBackend
        from refget.store import RefgetStore

        _LOGGER.info(f"Store changed, reloading from {self.store_url}")
        store = RefgetStore.open_remote(self.cache_dir, self.store_url)
        app.state.backend = RefgetStoreBackend(store)
