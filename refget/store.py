"""
RefgetStore and related exports from gtars.

This module re-exports the Rust-based gtars.refget components
for local sequence collection storage and FASTA processing.
"""

from .const import GTARS_INSTALLED

if GTARS_INSTALLED:
    from gtars.refget import (
        RefgetStore,
        StorageMode,
        digest_fasta,
        compute_fai,
        digest_sequence,
        SequenceCollection,
    )
else:
    RefgetStore = None
    StorageMode = None
    digest_fasta = None
    compute_fai = None
    digest_sequence = None
    SequenceCollection = None

__all__ = [
    "RefgetStore",
    "digest_fasta",
    "StorageMode",
    "compute_fai",
    "digest_sequence",
    "SequenceCollection",
    "GTARS_INSTALLED",
]
