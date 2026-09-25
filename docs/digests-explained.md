# What are refget digests?

GA4GH refget digests are content-addressable identifiers for biological sequences and sequence collections, such as reference genomes. Instead of relying on arbitrary names like "chr1" or "GRCh38", digests identify sequences by their actual content using cryptographic hashes.

## Why use content-addressable identifiers?

- **Reproducibility**: The same sequence always produces the same digest, regardless of where or when it's computed
- **Interoperability**: Different databases can identify the same sequences without coordinating naming conventions
- **Verification**: Confirm that two files contain identical sequences by comparing their digests

## Digest formats

The refget standards define two types of digests:

### Refget Sequence digests

Individual sequences are identified with the `SQ.` prefix:

```
SQ.YBbVX0dLKG1ieEDCiMmkrTZFt_Z5Vdaj
```

This digest is computed by:
1. Taking the uppercase sequence string (e.g., "ACGT...")
2. Computing a SHA-512 hash
3. Truncating to 24 bytes
4. Base64url encoding the result

### Refget Sequence Collection digests

Sequence collections (groups of sequences, like a genome assembly) use unprefixed digests:

```
XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk
```

Collection digests are computed from the digests of their component attributes (names and sequences), making them a reflection of the entire collection's content.

## Levels of representation

Sequence collections can be represented at different levels of detail:

| Level | Contents | Use case |
|-------|----------|----------|
| Level 0 | Just the top-level digest | Quick identification |
| Level 1 | Digests of each attribute array | Comparing what changed |
| Level 2 | Full arrays (names, lengths, sequences) | Complete information |

## Learn more

- [Getting started tutorial](using-services/getting-started.py) - Quick walkthrough of computing your first digest
- [Computing digests locally](using-services/digests.ipynb) - Tutorial on computing digests
- [GA4GH refget specification](https://ga4gh.github.io/refget/) - Official specification
