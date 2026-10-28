# HGVS Parsing API Reference

The gtars HGVS module parses Human Genome Variation Society (HGVS) variant nomenclature and converts variants to GA4GH VRS (Variant Representation Specification) identifiers. This enables reproducible variant identification across systems.

## Supported HGVS Syntax

### Reference Types

| Prefix | Description | Example |
|--------|-------------|---------|
| `g.` | Genomic | `NC_000007.14:g.140753336A>T` |
| `c.` | Coding transcript | `NM_004333.6:c.1799T>A` |
| `n.` | Non-coding transcript | `NR_046018.2:n.100A>G` |
| `m.` | Mitochondrial | `NC_012920.1:m.8993T>G` |
| `r.` | RNA | `NM_004333.6:r.1799u>a` |

### Edit Types

| Edit | Syntax | Description |
|------|--------|-------------|
| Substitution | `A>T` | Single nucleotide change |
| Deletion | `del` or `delATG` | Sequence removal |
| Insertion | `insATG` | Sequence insertion |
| Deletion-insertion | `delinsATG` or `delATGinsCT` | Combined deletion and insertion |
| Duplication | `dup` or `dupA` | Sequence duplication |

### Position Notation

| Notation | Example | Description |
|----------|---------|-------------|
| Simple | `123` | Position 123 |
| Range | `123_456` | Positions 123 through 456 |
| Intronic (downstream) | `93+1` | 1 base into intron after exon position 93 |
| Intronic (upstream) | `93-1` | 1 base into intron before exon position 93 |
| 5' UTR | `-14` | 14 bases upstream of CDS start |
| 3' UTR | `*37` | 37 bases downstream of CDS end |

### Not Supported

- `p.` (protein variants)
- Repeat notation (`[3]`, `[5_10]`)
- Complex variants with multiple changes
- Mosaic/chimeric notation

---

## Rust API

### Parsing HGVS Strings

```rust
use gtars_vrs::hgvs::{parse, HgvsVariant, ReferenceType};

let variant = parse("NC_000007.14:g.140753336A>T")?;

assert_eq!(variant.accession, "NC_000007.14");
assert_eq!(variant.reference_type, ReferenceType::G);
```

### HgvsVariant Struct

```rust
pub struct HgvsVariant<'a> {
    /// Reference sequence accession (e.g., "NC_000007.14", "NM_004333.6")
    /// OR gene symbol if no accession provided (e.g., "BRAF")
    pub accession: &'a str,

    /// Reference type (g., c., n., m., r., p.)
    pub reference_type: ReferenceType,

    /// Position and edit information
    pub posedit: PosEdit<'a>,

    /// Optional gene symbol in parentheses (e.g., "(BRAF)")
    pub gene: Option<&'a str>,
}
```

### Position Struct

```rust
pub struct Position {
    /// Base position (1-based in HGVS; negative for 5' UTR)
    pub base: i64,

    /// Intronic offset (+ enters downstream intron, - enters upstream intron)
    pub offset: i64,

    /// Reference point for the position
    pub datum: Datum,
}

pub enum Datum {
    SeqStart,   // Position relative to sequence start (g., n., m.)
    CdsStart,   // Position relative to CDS start (c.)
    CdsEnd,     // Position relative to CDS end (c.*N)
}
```

### TranscriptProvider Trait

Required for converting `c.` and `n.` variants to genomic coordinates:

```rust
pub trait TranscriptProvider {
    /// Map a transcript position to a genomic coordinate
    fn tx_to_genome(
        &self,
        tx_accession: &str,
        position: &Position,
    ) -> Result<(u64, String), HgvsError>;

    /// Get the strand of a transcript (+1 or -1)
    fn tx_strand(&self, tx_accession: &str) -> Result<i8, HgvsError>;

    /// Get the genomic reference accession for a transcript
    fn tx_accession_to_genomic(&self, tx_accession: &str) -> Result<String, HgvsError>;

    /// Resolve a gene symbol to its MANE Select transcript accession
    fn gene_to_mane_accession(&self, gene: &str) -> Option<String>;
}
```

### ReftxProvider

Implementation of `TranscriptProvider` backed by a transcript store:

```rust
use gtars_reftx::ReftxStore;
use gtars_vrs::hgvs::ReftxProvider;

let store = ReftxStore::open("path/to/reftx.bin")?;
let provider = ReftxProvider::new(&store);

// Convert c. variant using MANE lookup
let (g_pos, chrom) = provider.tx_to_genome("BRAF", &position)?;
```

### Converting to VRS Allele

```rust
use gtars_vrs::hgvs::{parse, to_vrs_allele};
use gtars_refget::RefgetStore;

let variant = parse("NC_000007.14:g.140753336A>T")?;

let mut refget_store = RefgetStore::open("path/to/store")?;
let allele = to_vrs_allele(
    &variant,
    &mut refget_store,
    "collection_digest",
    &provider,
)?;

println!("VRS ID: {}", allele.compute_id());
```

### Convenience Function

```rust
use gtars_vrs::hgvs::hgvs_to_vrs_id;

let vrs_id = hgvs_to_vrs_id(
    "NC_000007.14:g.140753336A>T",
    &mut refget_store,
    "collection_digest",
    &provider,
)?;

// Returns: "ga4gh:VA.xxxxx"
```

---

## Python API

### Imports

```python
from gtars.vrs.hgvs import parse_hgvs, hgvs_to_vrs_id
from gtars.reftx import TxStore
```

### Parse and Inspect HGVS

```python
variant = parse_hgvs("NC_000007.14:g.140753336A>T")

print(variant.accession)        # "NC_000007.14"
print(variant.reference_type)   # "g"
print(variant.position)         # 140753336
print(variant.edit)             # "A>T"
```

Output:

```
NC_000007.14
g
140753336
A>T
```

### Convert Genomic Variant to VRS ID

```python
from gtars.vrs.hgvs import hgvs_to_vrs_id
from gtars.refget import RefgetStore

store = RefgetStore("path/to/store")

vrs_id = hgvs_to_vrs_id(
    "NC_000007.14:g.140753336A>T",
    store=store,
    collection="GRCh38"
)

print(vrs_id)
```

Output:

```
ga4gh:VA.7kHvwqLrmJqO3hVZ0CqYzCJeVQF_1DYn
```

### Convert Coding Variant to VRS ID

Coding variants require a transcript store for coordinate mapping:

```python
from gtars.vrs.hgvs import hgvs_to_vrs_id
from gtars.refget import RefgetStore
from gtars.reftx import TxStore

refget_store = RefgetStore("path/to/store")
tx_store = TxStore("path/to/reftx.bin")

vrs_id = hgvs_to_vrs_id(
    "NM_004333.6:c.1799T>A",
    store=refget_store,
    collection="GRCh38",
    tx_store=tx_store
)

print(vrs_id)
```

Output:

```
ga4gh:VA.7kHvwqLrmJqO3hVZ0CqYzCJeVQF_1DYn
```

### Use MANE Lookup with Gene Symbol

When a gene symbol is provided instead of a transcript accession, the system automatically resolves to the MANE Select transcript:

```python
vrs_id = hgvs_to_vrs_id(
    "BRAF:c.1799T>A",
    store=refget_store,
    collection="GRCh38",
    tx_store=tx_store
)

# Internally resolves BRAF -> NM_004333.6, then maps c.1799 -> chr7:140753336
print(vrs_id)
```

Output:

```
ga4gh:VA.7kHvwqLrmJqO3hVZ0CqYzCJeVQF_1DYn
```

---

## CLI Commands

### hgvs-to-vrs

Convert HGVS notation to VRS ID:

```bash
gtars hgvs-to-vrs "NC_000007.14:g.140753336A>T" --store /path/to/store --collection GRCh38
```

Output:

```
ga4gh:VA.7kHvwqLrmJqO3hVZ0CqYzCJeVQF_1DYn
```

**Options:**

| Option | Description |
|--------|-------------|
| `--store, -s` | Path to RefgetStore |
| `--collection, -c` | Collection digest or name |
| `--tx-store, -t` | Path to transcript store (required for c./n. variants) |
| `--output, -o` | Output format: `id` (default), `json`, `allele` |

### Batch Processing

Process multiple HGVS variants from a file:

```bash
gtars hgvs-to-vrs --input variants.txt --store /path/to/store --collection GRCh38 --tx-store /path/to/reftx.bin
```

Input file format (one HGVS per line):

```
NC_000007.14:g.140753336A>T
NM_004333.6:c.1799T>A
BRAF:c.1799T>A
```

Output:

```
NC_000007.14:g.140753336A>T	ga4gh:VA.7kHvwqLrmJqO3hVZ0CqYzCJeVQF_1DYn
NM_004333.6:c.1799T>A	ga4gh:VA.7kHvwqLrmJqO3hVZ0CqYzCJeVQF_1DYn
BRAF:c.1799T>A	ga4gh:VA.7kHvwqLrmJqO3hVZ0CqYzCJeVQF_1DYn
```

### JSON Output

```bash
gtars hgvs-to-vrs "NC_000007.14:g.140753336A>T" --store /path/to/store --collection GRCh38 --output json
```

Output:

```json
{
  "hgvs": "NC_000007.14:g.140753336A>T",
  "vrs_id": "ga4gh:VA.7kHvwqLrmJqO3hVZ0CqYzCJeVQF_1DYn",
  "allele": {
    "location": {
      "sequenceReference": {
        "refgetAccession": "SQ.F-LrLMe1SRpfUZHkQmvkVgo2azJq"
      },
      "start": 140753335,
      "end": 140753336
    },
    "state": {
      "sequence": "T"
    }
  }
}
```

---

## Examples

### SNV (Single Nucleotide Variant)

```python
# BRAF V600E mutation
vrs_id = hgvs_to_vrs_id("NC_000007.14:g.140753336A>T", store=store, collection="GRCh38")
```

### Coding Variant

```python
# Same mutation in coding coordinates
vrs_id = hgvs_to_vrs_id(
    "NM_004333.6:c.1799T>A",
    store=store,
    collection="GRCh38",
    tx_store=tx_store
)
```

### Intronic Variant

```python
# Splice site variant
vrs_id = hgvs_to_vrs_id(
    "NM_004333.6:c.93+1G>A",
    store=store,
    collection="GRCh38",
    tx_store=tx_store
)
```

### Deletion

```python
# 3-base deletion
vrs_id = hgvs_to_vrs_id(
    "NC_000007.14:g.140753336_140753338del",
    store=store,
    collection="GRCh38"
)
```

### Gene Symbol with MANE Lookup

```python
# Uses MANE Select transcript (NM_004333.6) for BRAF
vrs_id = hgvs_to_vrs_id(
    "BRAF:c.1799T>A",
    store=store,
    collection="GRCh38",
    tx_store=tx_store
)
```

---

## Error Types

### HgvsError Enum

```rust
pub enum HgvsError {
    /// HGVS string could not be parsed
    ParseError { input: String, detail: String },

    /// Reference sequence not found in collection
    AccessionNotFound { accession: String, collection: String },

    /// Transcript not found in transcript store
    TranscriptNotFound(String),

    /// Gene has no MANE Select transcript
    NoManeTranscript { gene: String },

    /// Attempted c./n. conversion without a transcript provider
    NoTranscriptProvider { accession: String },

    /// Coordinate mapping failed
    MappingError { accession: String, detail: String },

    /// Reference type not supported (e.g., p.)
    UnsupportedReferenceType(ReferenceType),

    /// Edit type not supported (e.g., inv)
    UnsupportedEdit(String),

    /// Refget store operation failed
    RefgetError(String),
}
```

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ParseError` | Invalid HGVS syntax | Check variant notation against HGVS specification |
| `AccessionNotFound` | Accession not in collection | Verify accession matches reference assembly |
| `TranscriptNotFound` | Transcript not in store | Ensure transcript store includes the accession |
| `NoManeTranscript` | Gene has no MANE designation | Use specific transcript accession instead of gene symbol |
| `NoTranscriptProvider` | c./n. variant without transcript store | Provide `tx_store` parameter |
| `MappingError` | Position outside transcript bounds | Check position is valid for the transcript |

### Python Exception Handling

```python
from gtars.vrs.hgvs import hgvs_to_vrs_id, HgvsError

try:
    vrs_id = hgvs_to_vrs_id("INVALID:c.123A>T", store=store, collection="GRCh38")
except HgvsError as e:
    print(f"HGVS error: {e}")
```
