"""
RefgetStore and related exports from gtars.

This module re-exports the Rust-based gtars.refget components
for local sequence collection storage and FASTA processing.
"""

from .const import GTARS_INSTALLED

if GTARS_INSTALLED:
    from gtars.refget import RefgetStore, digest_fasta, StorageMode
else:
    RefgetStore = None
    digest_fasta = None
    StorageMode = None

__all__ = [
    "RefgetStore",
    "digest_fasta",
    "StorageMode",
    "GTARS_INSTALLED",
]
