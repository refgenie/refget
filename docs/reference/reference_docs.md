# Refget Python API Documentation

### FASTA Processing

::: refget.utils.fasta_to_seqcol_dict
    options:
      heading_level: 3

::: refget.utils.compare_seqcols
    options:
      heading_level: 3

::: refget.utils.calc_jaccard_similarities
    options:
      heading_level: 3

::: refget.utils.validate_seqcol
    options:
      heading_level: 3

::: refget.utils.validate_seqcol_bool
    options:
      heading_level: 3

### FastAPI Integration

::: refget.router.create_refget_router
    options:
      heading_level: 3

## Client Classes

The client module provides interfaces for interacting with refget-compliant servers.

::: refget.clients.SequenceClient
    options:
      show_source: true
      show_signature: true
      heading_level: 3

::: refget.clients.SequenceCollectionClient
    options:
      show_source: true
      show_signature: true
      heading_level: 3

::: refget.clients.FastaDrsClient
    options:
      show_source: true
      show_signature: true
      heading_level: 3

::: refget.clients.PangenomeClient
    options:
      show_source: true
      show_signature: true
      heading_level: 3

## Agent Classes

Agents provide higher-level abstractions for working with refget data in a PostgreSQL database.

::: refget.agents.RefgetDBAgent
    options:
      show_signature: true
      heading_level: 3

::: refget.agents.SequenceCollectionAgent
    options:
      heading_level: 3

::: refget.agents.SequenceAgent
    options:
      heading_level: 3

::: refget.agents.PangenomeAgent
    options:
      heading_level: 3

::: refget.agents.AttributeAgent
    options:
      heading_level: 3

::: refget.agents.FastaDrsAgent
    options:
      heading_level: 3

## RefgetStore (gtars)

RefgetStore provides high-performance local sequence storage implemented in Rust. It supports:

- **In-memory and on-disk storage** with optional compression
- **Remote store access** with local caching
- **Sequence retrieval** by digest or by collection + name
- **BED file region extraction** for batch operations
- **FASTA export** for individual sequences or regions

See the [RefgetStore tutorial](../using-services/refgetstore.py) for usage examples.

`RefgetStore`, `digest_fasta`, `compute_fai`, `digest_sequence`, `SequenceCollection`, `StorageMode`, and `sha512t24u_digest` are implemented in Rust in [gtars](https://docs.bedbase.org/gtars/refget/) and re-exported by refget. Their API reference is in the gtars docs: [gtars refget API reference](https://docs.bedbase.org/gtars/python/refget-api/).

## Digest Functions

Low-level functions for computing GA4GH digests:

::: refget.utils.canonical_str
    options:
      heading_level: 3
