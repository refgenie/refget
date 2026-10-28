# Data Models

The `refget` package uses Pydantic and SQLModel for data validation and database ORM. These models represent the core data structures for sequence collections, DRS objects, and related metadata.

!!! success "Data models"
    Data Models are only needed if you want to develop new packages that rely on the refget Python API.


## Model hierarchy

```
DrsObject (base)
└── FastaDrsObject (table)

SQLModel (base)
├── SequenceCollection (table)
├── Pangenome (table)
├── Sequence (table)
├── AccessMethod
├── AccessURL
└── Checksum
```

## Core Models

### SequenceCollection

The primary model representing a GA4GH sequence collection.

::: refget.models.SequenceCollection
    options:
      show_source: true
      show_signature: true
      heading_level: 4

### FastaDrsObject

A DRS object specialized for FASTA files, storing file metadata and FAI index information.

::: refget.models.FastaDrsObject
    options:
      show_source: true
      show_signature: true
      heading_level: 4

### DrsObject

Base model for GA4GH Data Repository Service (DRS) objects.

::: refget.models.DrsObject
    options:
      show_source: true
      show_signature: true
      heading_level: 4

### Pangenome

A collection of sequence collections representing a pangenome.

::: refget.models.Pangenome
    options:
      show_source: true
      show_signature: true
      heading_level: 4

### Sequence

An individual sequence with its digest and content.

::: refget.models.Sequence
    options:
      show_source: true
      show_signature: true
      heading_level: 4

## Supporting Models

### AccessMethod

Describes how to access object bytes (protocol type, URL, region).

::: refget.models.AccessMethod
    options:
      show_source: true
      show_signature: true
      heading_level: 4

### AccessURL

A fully resolvable URL with optional headers for authentication.

::: refget.models.AccessURL
    options:
      show_source: true
      show_signature: true
      heading_level: 4

### Checksum

A checksum for data integrity verification.

::: refget.models.Checksum
    options:
      show_source: true
      show_signature: true
      heading_level: 4

## Response Models

### PaginationResult

Pagination metadata for list endpoints.

::: refget.models.PaginationResult
    options:
      show_source: true
      show_signature: true
      heading_level: 4

### ResultsSequenceCollections

Paginated sequence collection results.

::: refget.models.ResultsSequenceCollections
    options:
      show_source: true
      show_signature: true
      heading_level: 4

### Similarities

Results from Jaccard similarity calculations.

::: refget.models.Similarities
    options:
      show_source: true
      show_signature: true
      heading_level: 4

## Attribute Tables

These models store individual attributes of sequence collections in normalized database tables:

### NamesAttr

::: refget.models.NamesAttr
    options:
      heading_level: 4

### LengthsAttr

::: refget.models.LengthsAttr
    options:
      heading_level: 4

### SequencesAttr

::: refget.models.SequencesAttr
    options:
      heading_level: 4

### NameLengthPairsAttr

::: refget.models.NameLengthPairsAttr
    options:
      heading_level: 4

## Usage Examples

### Creating a SequenceCollection from a FASTA file

```python
from refget.models import SequenceCollection

# From a FASTA file (requires gtars)
seqcol = SequenceCollection.from_fasta_file("genome.fa")

# Access different representations
print(seqcol.digest)  # Top-level digest
print(seqcol.level1())  # Attribute digests
print(seqcol.level2())  # Full arrays
print(seqcol.itemwise())  # Per-sequence dicts
```

### Creating a SequenceCollection from a dictionary

```python
from refget.models import SequenceCollection

seqcol_dict = {
    "names": ["chr1", "chr2"],
    "lengths": [1000, 2000],
    "sequences": ["SQ.abc123...", "SQ.def456..."]
}

seqcol = SequenceCollection.from_dict(seqcol_dict)
```

### Creating a FastaDrsObject

```python
from refget.models import FastaDrsObject

# From a FASTA file
drs_obj = FastaDrsObject.from_fasta_file("genome.fa")

# Access DRS metadata
print(drs_obj.id)  # Sequence collection digest
print(drs_obj.size)  # File size in bytes
print(drs_obj.checksums)  # SHA-256, MD5
print(drs_obj.access_methods)  # How to download
```
