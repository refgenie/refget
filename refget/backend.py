"""
SeqColBackend protocol and RefgetStoreBackend implementation.

The SeqColBackend protocol defines the interface for serving seqcol API endpoints.
Two implementations:
- RefgetDBAgent (PostgreSQL) — full features including similarities, pangenomes, DRS
- RefgetStoreBackend (RefgetStore) — core seqcol operations, no database required
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .const import DEFAULT_TRANSIENT_ATTRS
from .utils import calc_jaccard_similarities, compare_seqcols


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

    def list_attributes(self, attribute: str, page: int = 0, page_size: int = 100) -> dict:
        """List unique attribute digests. Returns {"results": [...], "pagination": {...}}"""
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
            store: A RefgetStore instance from gtars. Do NOT pass a
                ReadonlyRefgetStore — it cannot lazy-load collections.
        """
        self._store = store

    def get_collection(self, digest: str, level: int = 2) -> dict:
        try:
            if level == 1:
                result = self._store.get_collection_level1(digest)
            else:
                result = self._get_enriched_level2(digest)
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
        if attribute_name in DEFAULT_TRANSIENT_ATTRS:
            raise KeyError(
                f"Transient attribute '{attribute_name}' is not served via /attribute endpoint"
            )
        result = self._store.get_attribute(attribute_name, attribute_digest)
        if result is None:
            raise KeyError(f"Attribute {attribute_name}/{attribute_digest} not found")
        return result

    def _get_enriched_level2(self, digest: str) -> dict:
        """Get level 2 enriched with derived attributes (name_length_pairs, sorted_sequences).

        The store's get_collection_level2 only returns core attributes (names, lengths,
        sequences). For comparison, we need the derived attributes too. We get them
        from level 1 digests and resolve each via get_attribute.
        """
        try:
            level2 = self._store.get_collection_level2(digest)
        except (OSError, IOError):
            raise ValueError(f"Collection '{digest}' not found")
        if level2 is None:
            raise ValueError(f"Collection '{digest}' not found")
        try:
            level1 = self._store.get_collection_level1(digest)
        except (OSError, IOError):
            return level2
        # Add derived attributes that exist in level 1 but not level 2
        for attr in ["name_length_pairs", "sorted_sequences"]:
            if attr in level1 and attr not in level2:
                try:
                    resolved = self._store.get_attribute(attr, level1[attr])
                    if resolved is not None:
                        level2[attr] = resolved
                except Exception:
                    pass
        return level2

    def compare_digests(self, digest_a: str, digest_b: str) -> dict:
        level2_a = self._get_enriched_level2(digest_a)
        level2_b = self._get_enriched_level2(digest_b)
        return compare_seqcols(level2_a, level2_b)

    def compare_digest_with_level2(self, digest: str, level2_b: dict) -> dict:
        """Compare a stored collection with a POSTed level2 dict.

        The store does not have a native compare_with_level2, so we retrieve
        enriched level2 for the stored collection and use the Python compare utility.
        """
        level2_a = self._get_enriched_level2(digest)
        return compare_seqcols(level2_a, level2_b)

    def list_collections(
        self, page: int = 0, page_size: int = 100, filters: dict | None = None
    ) -> dict:
        result = self._store.list_collections(page=page, page_size=page_size, filters=filters)
        # Extract digest strings from SequenceCollectionMetadata objects
        result["results"] = [r.digest if hasattr(r, "digest") else r for r in result["results"]]
        return result

    def list_attributes(self, attribute: str, page: int = 0, page_size: int = 100) -> dict:
        all_cols = self._store.list_collections(page=0, page_size=10000)
        unique_digests = set()
        for col in all_cols["results"]:
            digest = col.digest if hasattr(col, "digest") else col
            level1 = self._store.get_collection_level1(digest)
            if level1 and attribute in level1:
                unique_digests.add(level1[attribute])
        sorted_digests = sorted(unique_digests)
        start = page * page_size
        end = start + page_size
        return {
            "results": sorted_digests[start:end],
            "pagination": {"page": page, "page_size": page_size, "total": len(sorted_digests)},
        }

    def compute_similarities(
        self,
        seqcol: dict,
        page: int = 0,
        page_size: int = 50,
        target_digests: list[str] | None = None,
    ) -> dict:
        """Compute Jaccard similarities between a seqcol and collections in the store.

        Args:
            target_digests: If provided, only compare against these digests.
                If None, compares against all collections.
        """
        if target_digests:
            all_digests = list(dict.fromkeys(target_digests))  # deduplicate, preserve order
        else:
            all_cols = self._store.list_collections(page=0, page_size=10000)
            all_digests = [c.digest if hasattr(c, "digest") else c for c in all_cols["results"]]

        # Get aliases for human-readable names
        alias_map = {}
        for ns in self._store.list_collection_alias_namespaces():
            try:
                aliases = self._store.list_collection_aliases(ns)
                for a in aliases:
                    digest = a["digest"] if isinstance(a, dict) else a.digest
                    alias = a["alias"] if isinstance(a, dict) else a.alias
                    alias_map.setdefault(digest, []).append(alias)
            except Exception:
                pass

        similarities = []
        for digest in all_digests:
            try:
                level2 = self._store.get_collection_level2(digest)
                if level2 is None:
                    continue
                jaccard = calc_jaccard_similarities(seqcol, level2)
                similarities.append(
                    {
                        "digest": digest,
                        "human_readable_names": alias_map.get(digest, []),
                        "similarities": jaccard,
                    }
                )
            except Exception:
                continue

        # Sort by max similarity descending
        similarities.sort(
            key=lambda s: max(s["similarities"].values()) if s["similarities"] else 0,
            reverse=True,
        )

        total = len(similarities)
        start = page * page_size
        paged = similarities[start : start + page_size]

        return {
            "similarities": paged,
            "pagination": {"page": page, "page_size": page_size, "total": total},
            "reference_digest": None,
        }

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
