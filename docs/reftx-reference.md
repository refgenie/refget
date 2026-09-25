# RefgetTranscripts (reftx) Reference

RefgetTranscripts (reftx) is a compact binary transcript store for HGVS coordinate mapping. It finds a transcript with a binary search over a sorted hash index, so lookups are O(log n). A store can be read from disk with a memory map, with positioned reads (`pread`), or from bytes already in memory (which is how it runs in the browser).

The code lives in the `gtars-refget` crate, in the `gtars_refget::transcripts` module.

## Quick Example

```rust
use gtars_refget::transcripts::{ReadonlyTxStore, TxBackend, TxStoreBuilder};

// Chromosome digests are the 24 raw bytes behind a refget "SQ." accession.
let raw = base64_url::decode("<sha512t24u digest of chr7>").expect("valid base64url");
let chr7_digest: [u8; 24] = raw.as_slice().try_into()?;

// Build a store from cdot JSON
let mut builder = TxStoreBuilder::new();
builder.add_chrom_mapping("NC_000007.14", chr7_digest);
builder.load_mane_summary("MANE.GRCh38.v1.3.summary.txt.gz")?; // optional, load before ingest
builder.ingest_cdot("cdot.grch38.json.gz")?;
builder.build("transcripts.reftx")?;

// Open and query
let store = ReadonlyTxStore::open_with_backend("transcripts.reftx", TxBackend::Pread)?;

if let Some(tx) = store.lookup("NM_004333.6") {
    println!("{}: {} exons on {:?}", tx.accession, tx.exons.len(), tx.strand);
}
```

---

## Rust API

### Installation and features

Add `gtars-refget` with the `transcripts` feature:

```toml
[dependencies]
gtars-refget = { git = "https://github.com/databio/gtars", branch = "dev", features = ["transcripts"] }
```

The API is split in two by Cargo feature:

| Feature | What you get |
|---------|--------------|
| `transcripts` | The core, which works on every target including WASM: `ReadonlyTxStore` (with `from_bytes`), `TranscriptRef`, the models, `CoordinateMapper`, the mature mRNA helpers, and `build_reftx_bytes_in_memory` |
| `transcripts` + `filesystem` | Also the file-based parts: `TxStore`, `TxBackend`, `TxStoreBuilder`, and the `ReadonlyTxStore::open_*` constructors |

`filesystem` is on by default. For WASM, use `default-features = false, features = ["transcripts"]`.

All public types are re-exported from `gtars_refget::transcripts` (and from the crate root).

---

### ReadonlyTxStore

Immutable transcript store for read access. All lookups take `&self`, so one store can be shared across threads with `Arc<ReadonlyTxStore>`.

Every constructor checks the header and returns an error if the magic number or format version is wrong. Stores with fewer than 500,000 transcripts are fully decoded into memory when opened.

#### ReadonlyTxStore::open_with_backend

```rust
pub fn open_with_backend<P: AsRef<Path>>(path: P, backend: TxBackend) -> Result<Self>
```

Open a `.reftx` file with the backend you choose. Needs the `filesystem` feature.

**Parameters:**

- `path` - Path to a `.reftx` file
- `backend` - `TxBackend::Pread` or `TxBackend::Mmap`

#### TxBackend

```rust
pub enum TxBackend {
    Mmap,
    Pread,
}
```

- `Pread` - Positioned reads on the file. No memory mapping. The safe default for a single process.
- `Mmap` - Memory-map the whole file. Best when many processes read the same large store, since they share the OS page cache. The file must not be changed or truncated while it is mapped. The builder always writes files with an atomic rename, so this is safe for files it produced.

#### ReadonlyTxStore::open_mmap / open_pread

```rust
pub fn open_mmap<P: AsRef<Path>>(path: P) -> Result<Self>
pub fn open_pread<P: AsRef<Path>>(path: P) -> Result<Self>
```

Shortcuts for `open_with_backend` with a fixed backend. Need the `filesystem` feature.

#### ReadonlyTxStore::from_bytes

```rust
pub fn from_bytes(bytes: Vec<u8>) -> Result<Self>
```

Build a store from the full contents of a `.reftx` file held in memory. Uses no file system and no memory map, so it works on every target, including WASM.

**Example:**

```rust
let bytes = std::fs::read("transcripts.reftx")?;
let store = ReadonlyTxStore::from_bytes(bytes)?;
```

#### ReadonlyTxStore::len / is_empty

```rust
pub fn len(&self) -> u64
pub fn is_empty(&self) -> bool
```

Number of transcripts in the store, and whether it is zero.

#### ReadonlyTxStore::lookup

```rust
pub fn lookup(&self, accession: &str) -> Option<TranscriptRef<'_>>
```

Look up a transcript by accession. Uses an O(log n) binary search on the index.

**Parameters:**

- `accession` - Transcript accession with version (e.g., `"NM_004333.6"`)

**Returns:** `Option<TranscriptRef<'_>>` - A reference to the cached transcript, or a freshly decoded one

**Example:**

```rust
use std::sync::Arc;

let store = ReadonlyTxStore::open_pread("transcripts.reftx")?;
let shared = Arc::new(store);

// Multiple threads can call lookup at the same time
let tx = shared.lookup("NM_004333.6");
```

#### ReadonlyTxStore::lookup_mane

```rust
pub fn lookup_mane(&self, gene: &str) -> Option<Transcript>
```

Look up the MANE Select transcript for a gene symbol. The match ignores case (`"braf"` finds `"BRAF"`). Returns `None` if the gene has no MANE Select transcript, or if the store was built without MANE data.

**Parameters:**

- `gene` - Gene symbol (e.g., `"BRAF"`)

**Returns:** `Option<Transcript>` - An owned copy of the MANE Select transcript

#### ReadonlyTxStore::has_mane_index

```rust
pub fn has_mane_index(&self) -> bool
```

Returns true if the store has a MANE gene index, meaning `lookup_mane` can find anything.

---

### TranscriptRef

```rust
pub enum TranscriptRef<'a> {
    Cached(&'a Transcript),
    Owned(Transcript),
}
```

The value returned by `ReadonlyTxStore::lookup`. It derefs to `Transcript`, so you can read fields directly (`tx.accession`, `tx.exons`).

---

### TxStore

Mutable, memory-mapped store for the setup phase. Use it when you want to choose which transcripts are decoded ahead of time, then convert it to a `ReadonlyTxStore`. Needs the `filesystem` feature. If you just want to read a store, `ReadonlyTxStore::open_with_backend` is simpler.

#### TxStore::open / open_mmap

```rust
pub fn open<P: AsRef<Path>>(path: P) -> Result<Self>
pub fn open_mmap<P: AsRef<Path>>(path: P) -> Result<Self>
```

Open a store from disk with a memory map. `open` is the same as `open_mmap`. Returns an error if the magic number or version is invalid.

#### TxStore::len / is_empty

```rust
pub fn len(&self) -> u64
pub fn is_empty(&self) -> bool
```

#### TxStore::lookup

```rust
pub fn lookup(&self, accession: &str) -> Option<Transcript>
```

Look up a transcript by accession (O(log n) binary search). Returns an owned `Transcript`.

#### TxStore::ensure_decoded

```rust
pub fn ensure_decoded(&mut self, accession: &str) -> Result<()>
```

Decode one transcript into the internal cache ahead of time. The cache is carried into the `ReadonlyTxStore`.

#### TxStore::ensure_decoded_where

```rust
pub fn ensure_decoded_where<F>(&mut self, predicate: F) -> Result<usize>
where
    F: Fn(&Transcript) -> bool,
```

Decode all transcripts that match a predicate into the cache. Returns how many were cached.

**Example:**

```rust
// Pre-load all BRAF transcripts
let count = store.ensure_decoded_where(|tx| tx.gene == "BRAF")?;
```

#### TxStore::into_readonly

```rust
pub fn into_readonly(self) -> ReadonlyTxStore
```

Convert to a memory-mapped `ReadonlyTxStore`. If the store has fewer than 500,000 transcripts and nothing has been cached yet, this decodes every transcript into memory first.

#### TxStore::into_readonly_lazy

```rust
pub fn into_readonly_lazy(self) -> ReadonlyTxStore
```

Convert without decoding anything extra. Transcripts not already cached are decoded from the file on each lookup. Use this when only a few transcripts will be queried.

---

### TxStoreBuilder

Builds a `.reftx` file from cdot JSON. Needs the `filesystem` feature.

#### TxStoreBuilder::new

```rust
pub fn new() -> Self
```

Create an empty builder. `TxStoreBuilder::default()` does the same.

#### TxStoreBuilder::add_chrom_mapping

```rust
pub fn add_chrom_mapping(&mut self, name: &str, digest: [u8; 24])
```

Register a chromosome name and its refget digest. The digest is the 24 raw bytes of the sequence's sha512t24u digest (the part after `SQ.`, base64url-decoded).

**Parameters:**

- `name` - Chromosome name as it appears in the cdot file (e.g., `"NC_000001.11"`)
- `digest` - 24-byte refget digest

#### TxStoreBuilder::load_mane_summary

```rust
pub fn load_mane_summary<P: AsRef<Path>>(&mut self, path: P) -> Result<usize>
```

Load MANE flags from an NCBI MANE summary TSV (plain or `.gz`). It reads the `RefSeq_nuc`, `Ensembl_nuc`, and `MANE_status` columns, so both RefSeq and Ensembl transcripts get their flags.

Call this **before** `ingest_cdot`. Flags are attached to transcripts as they are ingested.

**Parameters:**

- `path` - Path to the MANE summary file

**Returns:** Count of accession entries loaded (RefSeq and Ensembl accessions are counted separately)

#### TxStoreBuilder::has_mane_flags

```rust
pub fn has_mane_flags(&self) -> bool
```

Returns true if any MANE flags have been loaded.

#### TxStoreBuilder::ingest_cdot

```rust
pub fn ingest_cdot<P: AsRef<Path>>(&mut self, path: P) -> Result<usize>
```

Ingest a cdot-style JSON file (plain or `.json.gz`). Skips transcripts whose chromosome was not registered with `add_chrom_mapping`, transcripts with a strand other than 1 or -1, and transcripts with no exons.

The reader expects a top-level `transcripts` object. Each entry needs `id`, `contig`, `strand`, and `exons` (a list of `[start, end]` pairs), plus optional `gene_name`, `cds_start`, and `cds_end`.

**Parameters:**

- `path` - Path to the JSON file

**Returns:** Count of transcripts ingested

#### TxStoreBuilder::len / is_empty

```rust
pub fn len(&self) -> usize
pub fn is_empty(&self) -> bool
```

Number of transcripts staged so far. Transcripts can also be added directly through the public `transcripts: Vec<Transcript>` field.

#### TxStoreBuilder::build

```rust
pub fn build<P: AsRef<Path>>(&mut self, output: P) -> Result<()>
```

Write the binary store to disk. Returns an error if no transcripts are staged. The file is written to a temporary file and then renamed into place, so readers never see a half-written file. A `<output>.lock` file stops two builders from writing the same path at once.

**Parameters:**

- `output` - Output path for the `.reftx` file

**Example:**

```rust
let mut builder = TxStoreBuilder::new();
builder.add_chrom_mapping("NC_000007.14", chr7_digest);
builder.load_mane_summary("MANE.GRCh38.v1.3.summary.txt.gz")?;
let count = builder.ingest_cdot("cdot.grch38.json.gz")?;
println!("Ingested {} transcripts", count);
builder.build("transcripts.reftx")?;
```

#### build_reftx_bytes_in_memory

```rust
pub fn build_reftx_bytes_in_memory(transcripts: &[Transcript]) -> Result<Vec<u8>>
```

Build a complete `.reftx` image in memory, with no file system. Works on every target. Pair it with `ReadonlyTxStore::from_bytes`.

---

### Transcript

Transcript annotation record.

```rust
pub struct Transcript {
    /// Accession with version (e.g., "NM_004333.6")
    pub accession: String,
    /// Gene symbol (e.g., "BRAF")
    pub gene: String,
    /// Chromosome refget digest (24 bytes, truncated SHA-512)
    pub chrom_digest: [u8; 24],
    /// Strand orientation
    pub strand: Strand,
    /// CDS start in genomic coordinates (None if non-coding)
    pub cds_start: Option<u32>,
    /// CDS end in genomic coordinates (None if non-coding)
    pub cds_end: Option<u32>,
    /// Exons in genomic order (5' to 3' on chromosome)
    pub exons: Vec<Exon>,
    /// MANE Select / Plus Clinical status
    pub mane: ManeStatus,
}
```

**Methods:**

| Method | Return Type | Description |
|--------|-------------|-------------|
| `transcript_length()` | `u32` | Total transcript length (sum of exon lengths) |
| `cds_length()` | `u32` | CDS length in bases (0 if non-coding) |
| `is_coding()` | `bool` | Returns true if transcript has CDS |
| `accession_base()` | `&str` | Accession without version (e.g., `"NM_004333"`) |

### Exon

A single exon with genomic coordinates.

```rust
pub struct Exon {
    /// Genomic start (0-based, inclusive)
    pub start: u32,
    /// Genomic end (0-based, exclusive)
    pub end: u32,
}
```

**Methods:**

| Method | Return Type | Description |
|--------|-------------|-------------|
| `len()` | `u32` | Length in bases |
| `is_empty()` | `bool` | Returns true if zero-length |

### Strand

Strand orientation.

```rust
pub enum Strand {
    Forward = 1,
    Reverse = -1,
}
```

`Strand::from_i8(1)` and `Strand::from_i8(-1)` parse a strand; any other value gives `None`.

### ManeStatus

MANE flags for a transcript. The default is both flags false.

```rust
pub struct ManeStatus {
    /// True if this is the MANE Select transcript for its gene
    pub mane_select: bool,
    /// True if this is MANE Plus Clinical
    pub mane_clinical: bool,
}
```

`is_mane()` returns true if either flag is set.

---

### CoordinateMapper

Maps HGVS transcript coordinates to 0-based genomic positions, using a `ReadonlyTxStore`.

```rust
use gtars_refget::transcripts::CoordinateMapper;

let mapper = CoordinateMapper::new(&store);
let result = mapper.c_to_g("NM_004333.6", 1799)?;
println!("genomic position: {}", result.position);
```

| Method | Description |
|--------|-------------|
| `new(store: &ReadonlyTxStore)` | Create a mapper |
| `c_to_g(accession, c_pos: i64)` | Map `c.N` to genomic |
| `n_to_g(accession, n_pos: u64)` | Map `n.N` to genomic |
| `c_to_g_full(accession, c_pos: i64, offset: i64, is_cds_end: bool)` | Full `c.` form: negative `c_pos` for 5' UTR (`c.-14`), `offset` for introns (`c.93+5` is `offset = 5`), `is_cds_end = true` for 3' UTR (`c.*N`) |
| `n_to_g_full(accession, n_pos: i64, offset: i64)` | Full `n.` form with an intronic offset |
| `c_to_g_by_gene(gene, c_pos, offset, is_cds_end)` | Resolve the gene's MANE Select transcript, then map. Returns `(accession_used, MappingResult)` |
| `g_to_transcript_offset(accession, g_pos: u64)` | Map a genomic position to a 0-based offset on the spliced mRNA. Returns `Ok(None)` if the position is not in an exon |

The mapping methods return `Result<MappingResult, MappingError>`:

```rust
pub struct MappingResult {
    /// Genomic position (0-based)
    pub position: u64,
    /// Chromosome refget digest
    pub chrom_digest: [u8; 24],
}
```

`MappingError` covers cases such as `TranscriptNotFound`, `NoManeTranscript`, `OutsideCds`, `InvalidIntronicOffset`, the 5' and 3' UTR overflows, and `NonCodingTranscript`.

`CoordinateMapperWriter` has the same `new`, `c_to_g`, and `n_to_g` methods, but takes `&mut self` and reuses its internal buffers between calls. Use it in tight loops.

---

### Mature mRNA helpers

These build the spliced (mature) mRNA reference sequence for a transcript by reading exon sequences from a `ReadonlyRefgetStore`. Reverse-strand transcripts are reverse-complemented. The result is the reference sequence; variants are not applied.

```rust
pub fn mature_mrna(
    store: &ReadonlyRefgetStore,
    tx_store: &ReadonlyTxStore,
    accession: &str,
) -> Result<String>

pub fn mature_mrna_for_transcript(
    store: &ReadonlyRefgetStore,
    tx: &Transcript,
) -> Result<String>

pub fn concat_regions(
    store: &ReadonlyRefgetStore,
    chrom_digest: &[u8; 24],
    regions: &[(u32, u32)],
    strand: Strand,
) -> Result<String>
```

- `mature_mrna` looks up the accession, then builds its sequence.
- `mature_mrna_for_transcript` does the same for a transcript you already have.
- `concat_regions` is the building block: it joins any list of 0-based, half-open regions (in genomic order) from one chromosome.

They return an error if the transcript is missing, the chromosome is not in the sequence store, or an exon runs past the end of the chromosome (a sign that the transcripts and genome do not match).

**Example:**

```rust
use gtars_refget::store::RefgetStore;
use gtars_refget::transcripts::{mature_mrna, ReadonlyTxStore};

let seqs = RefgetStore::open_local("/data/refget")?.into_readonly();
let tx_store = ReadonlyTxStore::open_pread("transcripts.reftx")?;
let mrna = mature_mrna(&seqs, &tx_store, "NM_004333.6")?;
```

---

### TranscriptProvider and TxProvider

HGVS-to-VRS code in `gtars-vrs` reads transcripts through the `TranscriptProvider` trait (in `gtars_vrs::provider`, also re-exported at the `gtars_vrs` root):

```rust
pub trait TranscriptProvider {
    fn c_to_genomic(&self, accession: &str, c_pos: i64) -> Result<SequenceLocation, ProviderError>;
    fn n_to_genomic(&self, accession: &str, n_pos: u64) -> Result<SequenceLocation, ProviderError>;
    fn get_chrom_accession(&self, accession: &str) -> Result<String, ProviderError>;
    fn get_strand(&self, accession: &str) -> Result<i8, ProviderError>;
    fn c_to_genomic_full(&self, accession: &str, c_pos: i64, offset: i64, is_cds_end: bool)
        -> Result<SequenceLocation, ProviderError>;   // has a default
    fn n_to_genomic_full(&self, accession: &str, n_pos: i64, offset: i64)
        -> Result<SequenceLocation, ProviderError>;   // has a default
    fn gene_to_mane_accession(&self, gene: &str) -> Option<String>;   // default: None
}
```

With the `transcripts` feature of `gtars-vrs`, the trait is implemented for `ReadonlyTxStore` and for `TxProvider`, a cheap-to-clone wrapper around `Arc<ReadonlyTxStore>` for sharing one store across workers. `NoTranscriptProvider` is a stand-in that rejects all transcript lookups, for when you only expect `g.` variants.

```rust
use std::sync::Arc;
use gtars_refget::transcripts::ReadonlyTxStore;
use gtars_vrs::TxProvider;

let store = ReadonlyTxStore::open_pread("transcripts.reftx")?;
let provider = TxProvider::new(Arc::new(store));
let store_again = provider.store(); // &Arc<ReadonlyTxStore>
```

---

## Python API

### Installation

The reftx module is part of the gtars Python package (it is in the default build):

```bash
pip install gtars
```

```python
from gtars.reftx import ReadonlyTxStore, TxStoreBuilder, CoordinateMapper
```

### ReadonlyTxStore

#### Opening a store

```python
store = ReadonlyTxStore.open("transcripts.reftx")   # memory-mapped
print(len(store))
```

#### Looking up transcripts

```python
tx = store.lookup("NM_004333.6")
if tx:
    print(f"{tx.accession}: {tx.gene}, {len(tx.exons)} exons")
    print(f"CDS: {tx.cds_start}-{tx.cds_end}")
    print(f"Strand: {tx.strand}")
```

#### MANE lookups

```python
if store.has_mane_index():
    tx = store.lookup_mane("BRAF")   # case-insensitive
    if tx:
        print(f"MANE Select for BRAF: {tx.accession}")
```

#### Other methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_chrom_accession(accession)` | `str` or `None` | The chromosome's `SQ.` refget accession |
| `get_strand(accession)` | `Strand` or `None` | The transcript's strand |

### TxStoreBuilder

#### Building a store from cdot

```python
builder = TxStoreBuilder()

# Map chromosome names to refget accessions ("SQ.<digest>" or the bare digest)
builder.add_chrom_mapping("NC_000007.14", "SQ.<sha512t24u digest of chr7>")

# Optionally load MANE flags. Do this before loading cdot.
builder.load_mane_summary("MANE.GRCh38.v1.3.summary.txt.gz")

# Ingest cdot JSON (.gz is detected automatically)
count = builder.load_cdot("cdot.grch38.json.gz")
print(f"Ingested {count} transcripts")

# Build the store
builder.build("transcripts.reftx")
```

| Method | Description |
|--------|-------------|
| `add_chrom_mapping(name, accession)` | Register a chromosome name and its refget accession |
| `load_mane_summary(path)` | Load MANE flags; returns the count of entries loaded |
| `load_cdot(path)` | Ingest a cdot JSON file; returns the count ingested. `load_cdot_gz` is an alias |
| `add_transcript(value)` | Add one transcript, given a `Transcript` or a dict shaped like `Transcript.to_dict()` |
| `len(builder)` | Number of transcripts staged |
| `build(out_path)` | Write the `.reftx` file |

### CoordinateMapper

```python
mapper = CoordinateMapper(store)

pos = mapper.c_to_g("NM_004333.6", 1799)          # 0-based genomic position (int)
info = mapper.c_to_g_full("NM_004333.6", 1799)
# {"chrom": "SQ...", "chrom_accession": "SQ...", "genomic_pos": ..., "strand": Strand.Minus}

by_gene = mapper.c_to_g_by_gene("BRAF", 1799)     # same dict plus "accession"
```

| Method | Returns | Description |
|--------|---------|-------------|
| `c_to_g(accession, c_pos, datum=None)` | `int` | Map `c.` to genomic. Pass `datum=1` for a 3' UTR `c.*N` position |
| `n_to_g(accession, n_pos)` | `int` | Map `n.` to genomic |
| `c_to_g_full(accession, c_pos, datum=None)` | `dict` | Like `c_to_g`, plus chromosome and strand |
| `n_to_g_full(accession, n_pos)` | `dict` | Like `n_to_g`, plus chromosome and strand |
| `c_to_g_by_gene(gene, c_pos, datum=None)` | `dict` | Map through the gene's MANE Select transcript |

The Python mapper does not take intronic offsets. Mapping failures raise `gtars.reftx.MappingError`; store and builder failures raise `gtars.reftx.TxStoreError`.

### ReftxProvider

`ReftxProvider(store)` wraps a `ReadonlyTxStore` for the HGVS functions in `gtars.vrs.hgvs`:

```python
from gtars.reftx import ReadonlyTxStore, ReftxProvider
from gtars.vrs.hgvs import hgvs_to_vrs_id

provider = ReftxProvider(ReadonlyTxStore.open("transcripts.reftx"))
vrs_id = hgvs_to_vrs_id("NM_004333.6:c.1799T>A", provider, refget_store, collection_digest)
```

### Transcript object attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `accession` | `str` | Full accession with version |
| `gene` | `str` or `None` | Gene symbol (`None` if empty) |
| `chrom` | `str` | Chromosome refget accession (`"SQ.<digest>"`) |
| `strand` | `Strand` | `Strand.Plus` or `Strand.Minus` (`str()` gives `"+"` or `"-"`) |
| `cds_start` | `int` or `None` | CDS start position (0-based) |
| `cds_end` | `int` or `None` | CDS end position (0-based, exclusive) |
| `exons` | `list[Exon]` | Exons, each with `start` and `end` |
| `mane` | `ManeStatus` or `None` | Has `select` and `plus_clinical` flags; `None` if neither is set |

`Transcript.to_dict()` returns the same data as a plain dict.

---

## JavaScript (WASM) API

The `gtars-js` WASM package includes a transcript store for the browser. There is no file system in the browser, so you fetch the `.reftx` bytes yourself and pass them in. Inside, it uses `ReadonlyTxStore::from_bytes` wrapped in the same `TxProvider` used on native.

```javascript
import init, { TranscriptStore, hgvs_to_vrs_id_with_transcripts } from "gtars-js";
await init();

const reftxBytes = new Uint8Array(await (await fetch(reftxUrl)).arrayBuffer());
const tx = new TranscriptStore(reftxBytes);   // throws if the bytes are not a valid .reftx
console.log(tx.transcriptCount());

const id = hgvs_to_vrs_id_with_transcripts(
    "NM_004333.6:c.1799T>A", "chr7", chr7Bases, tx);
// -> "ga4gh:VA.<digest>"
```

| API | Description |
|-----|-------------|
| `new TranscriptStore(bytes)` | Load a store from a `Uint8Array` holding an uncompressed `.reftx` file |
| `transcriptCount()` | Number of transcripts in the store |
| `hgvs_to_vrs_id_with_transcripts(hgvs, sequenceName, sequenceBases, tx)` | HGVS to VRS ID, resolving `c.`/`n.` and gene symbols. The bases must be for the chromosome the transcript lies on |
| `RefgetStore.hgvs_to_vrs_id_with_transcripts(hgvs, tx)` | Same, but reads bases from a `RefgetStore` that already holds that chromosome |

---

## Binary Format Specification

The `.reftx` file format is a compact binary format built for O(log n) lookups. It is the same for all three backends (memory map, pread, and in-memory bytes).

### File Layout

```
+------------------------------------------------------------------------------+
| HEADER (40 bytes, fixed)                                                     |
+------------------------------------------------------------------------------+
| RECORDS (variable length, starts at byte 40, sorted by accession hash)       |
+------------------------------------------------------------------------------+
| ACCESSION INDEX (16 bytes per entry, starts at index_offset)                 |
+------------------------------------------------------------------------------+
| MANE GENE INDEX (optional, starts at mane_index_offset)                      |
+------------------------------------------------------------------------------+
```

### Header (40 bytes)

| Offset | Size | Type | Name | Description |
|--------|------|------|------|-------------|
| 0 | 4 | `[u8; 4]` | magic | `b"RFTX"` (0x52, 0x46, 0x54, 0x58) |
| 4 | 4 | `u32 LE` | version | Format version (currently 2) |
| 8 | 8 | `u64 LE` | record_count | Number of transcript records |
| 16 | 8 | `u64 LE` | index_offset | Byte offset to the accession index |
| 24 | 8 | `u64 LE` | mane_index_offset | Byte offset to the MANE gene index, or 0 if there is none |
| 32 | 8 | `[u8; 8]` | reserved | Zero-filled for future use |

### Record Format (variable length)

Each transcript record has the following structure:

| Offset | Size | Type | Name | Description |
|--------|------|------|------|-------------|
| +0 | 1 | `u8` | accession_len | Length of accession string (max 255) |
| +1 | N | `[u8; N]` | accession | UTF-8 accession string |
| +N+1 | 1 | `u8` | gene_len | Length of gene symbol (max 255) |
| +N+2 | M | `[u8; M]` | gene | UTF-8 gene symbol |
| ... | 24 | `[u8; 24]` | chrom_digest | Truncated refget digest |
| ... | 1 | `i8` | strand | +1 forward, -1 reverse |
| ... | 1 | `u8` | mane_flags | bit 0 = MANE Select, bit 1 = MANE Plus Clinical |
| ... | 4 | `u32 LE` | cds_start | 0xFFFFFFFF if None |
| ... | 4 | `u32 LE` | cds_end | 0xFFFFFFFF if None |
| ... | 2 | `u16 LE` | exon_count | Number of exons |
| ... | 8*exons | `[(u32, u32)]` | exons | (start, end) pairs, LE |

### Accession Index Format (16 bytes per entry)

The index is sorted by accession_hash in ascending order to enable binary search.

| Offset | Size | Type | Name | Description |
|--------|------|------|------|-------------|
| +0 | 8 | `u64 LE` | accession_hash | FNV-1a hash of accession bytes |
| +8 | 8 | `u64 LE` | record_offset | Byte offset of record in file |

### MANE Gene Index Format

Present only if at least one transcript is MANE Select. It starts with a `u64 LE` entry count, followed by 16-byte entries sorted by hash:

| Offset | Size | Type | Name | Description |
|--------|------|------|------|-------------|
| +0 | 8 | `u64 LE` | gene_hash | FNV-1a hash of the upper-cased gene symbol |
| +8 | 8 | `u64 LE` | record_offset | Byte offset of the MANE Select record |

### Hash Function

Both indexes use FNV-1a 64-bit hashing:

```rust
const FNV_OFFSET: u64 = 0xcbf29ce484222325;
const FNV_PRIME: u64 = 0x100000001b3;

fn fnv1a_64(data: &[u8]) -> u64 {
    let mut hash = FNV_OFFSET;
    for &byte in data {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}
```

### Sentinel Values

- `0xFFFFFFFF` (u32 max) indicates None for `cds_start` and `cds_end`
- `mane_index_offset = 0` means the file has no MANE gene index

### Version History

| Version | Changes |
|---------|---------|
| 1 | Initial format |
| 2 | Header grows to 40 bytes with `mane_index_offset`; each record gains a `mane_flags` byte; optional MANE gene index. Readers accept only version 2 |

---

## Design Rationale

### Why binary instead of JSON?

cdot JSON files must be fully parsed and held in memory before any lookup. The binary format avoids that:

- **Read only what you need**: With mmap or pread, only the parts of the file you touch are read
- **O(log n) lookup**: Binary search on a sorted index
- **Few allocations on hot paths**: Small stores are decoded once, and `CoordinateMapperWriter` reuses its buffers

### Why FNV-1a hashing?

FNV-1a is simple, fast, and deterministic. Hash collisions are handled by linear probing with full accession string comparison.

### Why 24-byte digests?

A refget sequence digest (sha512t24u) is the first 24 bytes of a SHA-512 hash. The familiar `SQ.` form is those 24 bytes written as 32 base64url characters. Storing the raw 24 bytes saves space, and encoding them again gives back the exact refget key.

### Why exons inline?

Storing exons directly in each record avoids pointer chasing and keeps related data contiguous for better cache locality.

### Why three backends?

The lookup code is the same for all of them; only the way bytes are read changes. Positioned reads are the safe default. Memory mapping lets many processes share one copy of a large store in the OS page cache. In-memory bytes need no file system, which is what makes the store work in WASM.

## See Also

- [cdot project](https://github.com/SACGF/cdot) - Source of transcript JSON data
- [MANE](https://www.ncbi.nlm.nih.gov/refseq/MANE/) - Matched Annotation from NCBI and EMBL-EBI
- [RefgetStore format](reference/refgetstore-format.md) - Sequence storage format
