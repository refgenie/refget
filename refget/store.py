"""
RefgetStore and related exports from gtars.

This module re-exports the Rust-based gtars.refget components
for local sequence collection storage and FASTA processing.

RefgetStore also provides namespace-based alias management:
  Sequence aliases: add_sequence_alias, get_sequence_by_alias,
    get_aliases_for_sequence, list_sequence_alias_namespaces,
    list_sequence_aliases, remove_sequence_alias, load_sequence_aliases
  Collection aliases: add_collection_alias, get_collection_by_alias,
    get_aliases_for_collection, list_collection_alias_namespaces,
    list_collection_aliases, remove_collection_alias, load_collection_aliases

FHR (FAIR Headers Reference genome) metadata is also exposed via FhrMetadata
and the store's set/get/remove/list/load_fhr_metadata methods.

ReadonlyRefgetStore is the read-only variant of RefgetStore. All of its methods
borrow ``&self`` (no mutable borrow), making it safe to share across threads for
concurrent server reads. It is obtained only via ``RefgetStore.into_readonly()``
and cannot lazy-load: the mutable RefgetStore must call ``load_all_collections()``
(and ``load_all_sequences()`` for sequence/substring serving) before conversion.
"""

from .const import GTARS_INSTALLED

if GTARS_INSTALLED:
    from gtars.refget import (
        FhrMetadata,
        ReadonlyRefgetStore,
        RefgetStore,
        SequenceCollection,
        StorageMode,
        compute_fai,
        digest_fasta,
        digest_sequence,
    )
else:
    FhrMetadata = None
    ReadonlyRefgetStore = None
    RefgetStore = None
    StorageMode = None
    digest_fasta = None
    compute_fai = None
    digest_sequence = None
    SequenceCollection = None

__all__ = [
    "FhrMetadata",
    "ReadonlyRefgetStore",
    "RefgetStore",
    "digest_fasta",
    "StorageMode",
    "compute_fai",
    "digest_sequence",
    "SequenceCollection",
    "GTARS_INSTALLED",
]
