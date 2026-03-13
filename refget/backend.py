"""
SeqColBackend protocol and RefgetStoreBackend implementation.

The SeqColBackend protocol defines the interface for serving seqcol API endpoints.
Two implementations:
- RefgetDBAgent (PostgreSQL) — full features including similarities, pangenomes, DRS
- RefgetStoreBackend (RefgetStore) — core seqcol operations, no database required
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .utils import compare_seqcols


@runtime_checkable
class SeqColBackend(Protocol):
    """Backend protocol for serving seqcol API endpoints."""

    def get_collection(self, digest: str, level: int = 2) -> dict:
        """Get a collection at level 1 or 2. Raises ValueError if not found."""
        ...

    def get_collection_attribute(self, digest: str, attribute: str) -> list:
        """Get a single attribute array from a collection. Raises ValueError if not found."""
        ...

    def get_collection_itemwise(self, digest: str, limit: int | None = None) -> list[dict]:
        """Get collection in itemwise format. Raises ValueError if not found."""
        ...

    def get_attribute(self, attribute_name: str, attribute_digest: str) -> list:
        """Get an attribute by its own digest. Raises KeyError if not found."""
        ...

    def compare_digests(self, digest_a: str, digest_b: str) -> dict:
        """Compare two collections by digest. Raises ValueError if not found."""
        ...

    def compare_digest_with_level2(self, digest: str, level2_b: dict) -> dict:
        """Compare a stored collection with a POSTed level2 dict. Raises ValueError if not found."""
        ...

    def list_collections(
        self, page: int = 0, page_size: int = 100, filters: dict | None = None
    ) -> dict:
        """List collections with pagination and optional attribute filters.
        Returns {"results": [...], "pagination": {...}}"""
        ...

    def collection_count(self) -> int:
        """Total number of collections."""
        ...

    def capabilities(self) -> dict:
        """Return backend capabilities for service-info."""
        ...


class RefgetStoreBackend:
    """SeqColBackend backed by a RefgetStore (no database)."""

    def __init__(self, store):
        """
        Args:
            store: A RefgetStore or ReadonlyRefgetStore instance from gtars.
        """
        self._store = store

    def get_collection(self, digest: str, level: int = 2) -> dict:
        try:
            if level == 1:
                result = self._store.get_collection_level1(digest)
            else:
                result = self._store.get_collection_level2(digest)
        except (OSError, IOError):
            raise ValueError(f"Collection '{digest}' not found")
        if result is None:
            raise ValueError(f"Collection '{digest}' not found")
        return result

    def get_collection_attribute(self, digest: str, attribute: str) -> list:
        level2 = self.get_collection(digest, level=2)
        if attribute not in level2:
            raise ValueError(f"Attribute '{attribute}' not found")
        return level2[attribute]

    def get_collection_itemwise(self, digest: str, limit: int | None = None) -> list[dict]:
        level2 = self.get_collection(digest, level=2)
        # Transpose: {"names": [a,b], "lengths": [1,2]} -> [{"names": a, "lengths": 1}, ...]
        keys = list(level2.keys())
        n = len(level2[keys[0]])
        if limit:
            n = min(n, limit)
        return [{k: level2[k][i] for k in keys} for i in range(n)]

    def get_attribute(self, attribute_name: str, attribute_digest: str) -> list:
        result = self._store.get_attribute(attribute_name, attribute_digest)
        if result is None:
            raise KeyError(f"Attribute {attribute_name}/{attribute_digest} not found")
        return result

    def compare_digests(self, digest_a: str, digest_b: str) -> dict:
        try:
            result = self._store.compare(digest_a, digest_b)
        except (OSError, IOError):
            raise ValueError("Collection not found")
        if result is None:
            raise ValueError("Collection not found")
        return result

    def compare_digest_with_level2(self, digest: str, level2_b: dict) -> dict:
        """Compare a stored collection with a POSTed level2 dict.

        The store does not have a native compare_with_level2, so we retrieve
        level2 for the stored collection and use the Python compare utility.
        """
        level2_a = self.get_collection(digest, level=2)
        return compare_seqcols(level2_a, level2_b)

    def list_collections(
        self, page: int = 0, page_size: int = 100, filters: dict | None = None
    ) -> dict:
        if filters:
            raise ValueError("Filtering by attribute is not supported by RefgetStore backend")
        return self._store.list_collections(page=page, page_size=page_size)

    def collection_count(self) -> int:
        result = self._store.list_collections(page=0, page_size=1)
        return result["pagination"]["total"]

    def capabilities(self) -> dict:
        stats = self._store.stats()
        n_collections = int(stats.get("n_collections", 0))
        n_sequences = int(stats.get("n_sequences", 0))
        return {
            "backend_type": "refget_store",
            "n_collections": n_collections,
            "n_sequences": n_sequences,
            "has_sequence_data": n_sequences > 0,
            "collection_alias_namespaces": self._store.list_collection_alias_namespaces(),
            "sequence_alias_namespaces": self._store.list_sequence_alias_namespaces(),
        }
