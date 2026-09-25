# What is RefgetTranscripts (reftx)?

RefgetTranscripts (reftx) is a high-performance binary store for transcript annotations, designed as a companion to RefgetStore. Where RefgetStore holds sequences, reftx holds the transcript models that describe how those sequences are organized into genes -- exon boundaries, coding regions, strand orientation, and the mapping between transcript coordinates and genome coordinates.

In Rust, reftx lives in the `gtars-refget` crate as the `gtars_refget::transcripts` module, behind the `transcripts` Cargo feature. Adding the `filesystem` feature (on by default) also turns on the file-based readers and the builder. Python users get it as `gtars.reftx`.

## Why reftx?

HGVS nomenclature is the standard for describing genetic variants in clinical and research contexts. An HGVS expression like `NM_004333.6:c.1799T>A` (the BRAF V600E mutation) uses transcript coordinates (`c.` notation) rather than genome coordinates (`g.` notation). Converting between these coordinate systems requires transcript annotation data: which exons belong to transcript NM_004333.6, where they fall on the chromosome, and where the coding sequence begins.

Existing solutions have significant limitations:

| Solution | How it works | Problems |
|----------|--------------|----------|
| **UTA** (biocommons) | PostgreSQL database | Requires database server setup, complex infrastructure, network latency for every lookup |
| **cdot** | JSON files | The whole JSON file must be parsed into memory before the first lookup, and repeated field names waste space |

Both approaches work, but neither scales well to high-throughput variant annotation where millions of variants need coordinate mapping.

reftx takes a different approach: a binary format built for random access with O(log n) lookups. A lookup only needs the index entries it visits and the one record it wants, and there is no text to parse. (For smaller stores, reftx chooses to decode every record once when the store opens; see "Pre-decoded cache" below.)

## How reftx relates to RefgetStore

reftx and RefgetStore are independent but linked stores:

- **RefgetStore** holds sequences, indexed by content digest (e.g., `SQ.abc123...` → `ACGT...`)
- **reftx** holds transcript models that reference those sequences by digest (e.g., `NM_004333.6` has `chrom: SQ.abc123...`)

Each transcript record in reftx stores a chromosome reference as a refget digest (the `SQ.xxx` identifier), not a chromosome name. This means:

- **No assembly ambiguity**: The transcript is explicitly tied to a specific sequence, not a name that might mean different things in different contexts
- **Cross-assembly lookup**: Given a transcript, you can retrieve its chromosome sequence from any RefgetStore that contains that digest
- **Deduplication**: If two assemblies share the same chromosome sequence (common for mitochondrial DNA), the same digest resolves to both

The stores are operationally independent. You can build and query an reftx store without a RefgetStore present, and vice versa. The linking happens at query time when you need both transcript structure and sequence content.

## The binary format

reftx uses a custom binary format (`.reftx` files) designed for random access. All integers are little-endian. The file has four sections, in this order:

**Header (40 bytes):**

| Offset | Type | Field |
|--------|------|-------|
| 0 | 4 bytes | Magic bytes `RFTX` |
| 4 | u32 | Format version (currently 2) |
| 8 | u64 | Record count |
| 16 | u64 | Byte offset of the accession index |
| 24 | u64 | Byte offset of the MANE index (0 if the file has none) |
| 32 | 8 bytes | Reserved (zero) |

**Records (variable length):** Records start right after the header and are stored in order of their accession hash. Each record contains, in order:
- Accession (1-byte length, then the string, e.g., `NM_004333.6`; at most 255 bytes)
- Gene symbol (1-byte length, then the string, e.g., `BRAF`; at most 255 bytes)
- Chromosome digest (24 raw bytes, the decoded refget `SQ.` digest)
- Strand (1 signed byte: +1 or -1)
- MANE flags (1 byte: bit 0 is MANE Select, bit 1 is MANE Plus Clinical)
- CDS start and CDS end (u32 each, genomic coordinates; `0xFFFFFFFF` means none, for non-coding transcripts)
- Exon count (u16), then each exon as a start/end pair (u32 each)

Exon and CDS coordinates are 0-based, half-open genome coordinates, and exons are stored in genome order regardless of strand.

**Accession index (16 bytes per entry, sorted by hash):** One entry per record. Each entry holds the FNV-1a 64-bit hash of the accession (u64) and the record's byte offset (u64).

**MANE index (optional):** Written only if at least one transcript is MANE Select. It starts with an entry count (u64), then 16-byte entries sorted by hash. Each entry holds the FNV-1a hash of the upper-cased gene symbol (u64) and the byte offset of that gene's MANE Select record (u64).

Two different strings can have the same hash. When a lookup finds a matching hash, it reads the record and checks the full accession (or gene symbol, for the MANE index). If that record is not the right one, it scans the neighboring index entries that share the same hash.

### Why this layout matters

**Random access**: A lookup only needs the index entries it visits during binary search, plus the record itself. With a memory map, the operating system pages in only those parts of the file, not the whole thing.

**O(log n) lookup**: The sorted index enables binary search. For a store with 200,000 transcripts, a lookup visits about 18 index entries (plus a few more in the rare case of a hash collision).

**No text parsing**: Unlike JSON, there is no text to parse. Every field is a fixed-size integer or a length-prefixed string at a known position, so decoding a record is just reading bytes in order.

**Compact**: No repeated field names (every JSON record repeats `"accession"`, `"gene"`, `"exons"`, etc.). Coordinates use u32 (4 bytes) rather than JSON numbers written as text.

### Three ways to read the same file

The lookup code reads bytes through one small interface, so the same `.reftx` layout works with three backends. Only how the bytes are fetched differs:

- **mmap** (native): memory-maps the whole file. Good for large stores shared by many processes, since they share the operating system's page cache.
- **pread** (native): reads just the bytes it needs with positioned file reads, with no memory map. A safe choice for small or single-process use.
- **In-memory** (all targets, including WASM): holds the whole file as bytes in memory. In the browser, JavaScript fetches the `.reftx` file and passes the bytes in.

The mmap and pread backends need the `filesystem` feature. The in-memory backend needs only `transcripts`, so it builds for WASM. The builder writes the file to a temporary path and then renames it into place, so readers never see a half-written file. This matters most for mmap, which requires the file not to change while it is mapped.

## Key concepts

### TxStore vs ReadonlyTxStore

reftx provides two store types that reflect a common pattern for concurrent access:

1. **Setup phase:** `TxStore` (mutable, single owner): open the file with mmap, validate the header, and optionally pre-decode chosen transcripts
2. **Convert:** Call `.into_readonly()` (or `.into_readonly_lazy()`) to get `ReadonlyTxStore`
3. **Query phase:** `ReadonlyTxStore` (immutable) wrapped in `Arc<>` for multi-threaded access

**TxStore** is used during the setup phase. It is native-only and mmap-backed. You can pre-decode specific transcripts with `ensure_decoded` or `ensure_decoded_where` before converting. Converting moves the memory map into the readonly store without copying it.

**ReadonlyTxStore** is the immutable form, safe for concurrent `&self` access. Wrap it in `Arc` to share across threads. All lookup methods take `&self`, never `&mut self`, so multiple threads can query simultaneously without locks.

You don't have to go through `TxStore`. A `ReadonlyTxStore` can also be opened directly with `open_mmap`, `open_pread`, or `open_with_backend` (native), or built from bytes with `from_bytes` (all targets, including WASM).

This separation follows Rust's ownership model: mutation happens in a single-threaded setup phase, then the data becomes immutable and shareable.

### Pre-decoded cache

For batch processing (annotating millions of variants), decoding the same record over and over adds up. So a `ReadonlyTxStore` can keep a cache of already-decoded `Transcript` structs:

- For stores with fewer than 500,000 records, every record is decoded into the cache when the store is opened (or when `into_readonly()` is called on a `TxStore` with an empty cache)
- A lookup that hits the cache returns a reference to the cached transcript, with no decoding
- A lookup that misses the cache (large stores, or a store made with `into_readonly_lazy()`) reads the record from the file and returns a newly decoded, owned `Transcript`

`lookup` returns a `TranscriptRef`, which covers both cases and can be used like a `&Transcript`.

### TranscriptProvider trait

The `gtars-vrs` crate defines a `TranscriptProvider` trait, which abstracts over transcript sources. HGVS code uses it to turn transcript coordinates (`c.` and `n.`) into genome locations:

```rust
pub trait TranscriptProvider {
    fn c_to_genomic(&self, accession: &str, c_pos: i64) -> Result<SequenceLocation, ProviderError>;
    fn n_to_genomic(&self, accession: &str, n_pos: u64) -> Result<SequenceLocation, ProviderError>;
    fn get_chrom_accession(&self, accession: &str) -> Result<String, ProviderError>;
    fn get_strand(&self, accession: &str) -> Result<i8, ProviderError>;
    // Plus methods with default bodies: c_to_genomic_full and
    // n_to_genomic_full (intronic offsets, c.*N), and gene_to_mane_accession.
}
```

`ReadonlyTxStore` implements this trait, and `gtars-vrs` also provides `TxProvider`, a thin wrapper around `Arc<ReadonlyTxStore>`. The same `TxProvider` is used on native targets and in WASM. Because HGVS code only talks to the trait, another transcript source could implement it without changing the HGVS logic.

## MANE Select integration

MANE (Matched Annotation from NCBI and EBI) Select transcripts are the authoritative "default" transcripts for clinical reporting. For each protein-coding gene, MANE Select designates exactly one RefSeq transcript and one Ensembl transcript that:

- Are identical at the exon/CDS level
- Represent the most clinically relevant isoform
- Are stable identifiers for variant reporting

reftx stores MANE status as a flags byte on each transcript record. The builder fills these flags from the NCBI MANE summary file. The optional MANE index maps each gene symbol to its MANE Select record, so `lookup_mane("BRAF")` returns the MANE Select transcript for BRAF without external lookups. Gene matching ignores case. For clinical variant annotation pipelines, this distinction matters: reporting a variant on the MANE Select transcript ensures consistency across labs and databases.

The MANE Plus Clinical set (additional transcripts for genes with clinically significant non-Select isoforms) is also tracked as a flag on each record. It is not part of the MANE index, so there is no by-gene lookup for it.

## See also

- [What is RefgetStore?](refgetstore-explained.md) -- The companion sequence store
- [Digests explained](digests-explained.md) -- How refget digests work
- [reftx reference](reftx-reference.md) -- API and CLI details
- [Getting started with refget](using-services/getting-started.py) -- Tutorial for sequence operations
