# RefgetStore File Format

The RefgetStore is a directory-based file format for storing reference genome sequences with content-addressable access via GA4GH refget digests. It provides efficient storage, deduplication, and retrieval of sequences across multiple genome assemblies.

## Overview

A RefgetStore is a self-contained directory that stores sequence data in individual files (one per sequence), sequence metadata (names, lengths, digests, alphabets), collection metadata (grouping sequences by genome assembly), and index files for efficient lookup.

## Directory Structure

```
refget-store/
├── rgstore.json                  # Store metadata and configuration
├── sequences.rgsi                # refget sequence index file, for all sequences
├── collections.rgci              # refget collection index file
├── sequences/                    # Sequence data files
│   ├── Ab/                       # Subdirectories by digest prefix
│   │   ├── AbCdEf123....seq     # Individual sequence file
│   │   └── AbXyZ789....seq
│   └── Xy/
│       └── XyZabc456....seq
├── collections/                  # Collection metadata
│   ├── collection1.rgsi          # Each collection is represented as a refget sequence index file
│   ├── collection1.fhr.json      # FHR sidecar metadata file (optional)
│   └── collection2.rgsi
└── aliases/                      # Human-readable name mappings
    ├── sequences/                # Sequence alias namespaces
    │   ├── insdc.tsv
    │   └── genbank.tsv
    └── collections/              # Collection alias namespaces
        ├── ncbi.tsv
        └── ucsc.tsv
```

## File Specifications

### rgstore.json

The root metadata file containing store configuration.

**Location:** `<store-root>/rgstore.json`

**Format:** JSON

**Schema:**
```json
{
  "version": 1,
  "seqdata_path_template": "sequences/%s2/%s.seq",
  "collections_path_template": "collections/%s.rgsi",
  "sequence_index": "sequences.rgsi",
  "collection_index": "collections.rgci",
  "mode": "Encoded",
  "created_at": "2025-01-15T10:30:00Z",
  "modified": "2025-03-02T18:04:11Z",
  "ancillary_digests": true,
  "attribute_index": false,
  "sequence_alias_namespaces": ["insdc", "genbank"],
  "collection_alias_namespaces": ["ncbi", "ucsc"],
  "sequences_digest": "9f2c...",
  "collections_digest": "1a7e...",
  "aliases_digest": "c30b...",
  "fhr_digest": "48d1...",
  "logical_sequence_bytes": 782345216
}
```

**Fields:**

- `version` (integer): Format version number (currently `1`)
- `seqdata_path_template` (string): Template for sequence file paths
    - `%s` = full digest string
    - `%s2` = first 2 characters of digest
    - `%s4` = first 4 characters of digest
    - Example: `"sequences/%s2/%s.seq"` → `"sequences/Ab/AbCdEf123....seq"`
- `collections_path_template` (string): Template for collection file paths
    - Example: `"collections/%s.rgsi"`
- `sequence_index` (string): Path to the sequence metadata index file
    - Default: `"sequences.rgsi"`
- `collection_index` (string, optional): Path to the collection metadata index file
    - Default: `"collections.rgci"`
- `mode` (string): Storage mode for sequence data
    - `"Raw"`: Uncompressed sequence data
    - `"Encoded"`: Bit-packed encoded sequences (space efficient)
- `created_at` (string): ISO 8601 timestamp of store creation
- `modified` (string, optional): RFC 3339 timestamp, updated on every index write
- `ancillary_digests` (boolean): Whether the ancillary collection digests (`name_length_pairs`, `sorted_name_length_pairs`, `sorted_sequences`) are computed and stored
    - Default: `true`
- `attribute_index` (boolean): Whether an on-disk attribute reverse index is maintained
    - Default: `false`
- `sequence_alias_namespaces` (array of strings, optional): List of available sequence alias namespace names (e.g., `["insdc", "genbank"]`)
- `collection_alias_namespaces` (array of strings, optional): List of available collection alias namespace names (e.g., `["ncbi", "ucsc"]`)
- `sequences_digest` (string, optional): SHA-256 digest of `sequences.rgsi`
- `collections_digest` (string, optional): SHA-256 digest of `collections.rgci`
- `aliases_digest` (string, optional): SHA-256 digest of the combined alias data
- `fhr_digest` (string, optional): SHA-256 digest of the combined FHR sidecar data
- `logical_sequence_bytes` (integer, optional): Total size in bytes of all sequence payloads, computed at index-write time as each sequence's length converted through the storage mode's bits-per-symbol
    - Lets a client report the store's data size without downloading `sequences.rgsi`
    - Excludes index files, alias files, FHR sidecars, and this manifest
    - Absent in manifests written before the field existed

The alias namespace lists are authoritative: a store loads exactly the alias namespaces the manifest advertises rather than scanning the `aliases/` directory. This makes local and remote behavior identical, since remote access cannot list a directory.

### sequences.rgsi

Master index of all sequences in the store.

**Location:** `<store-root>/sequences.rgsi`

**Format:** Tab-separated values (TSV)

**Schema:**
```
#name    length    alphabet    sha512t24u                md5                               description
chr1     248956422  dna2bit    AbCdEf123GhIjK...         a1b2c3d4e5f6...                   Homo sapiens chromosome 1
chr2     242193529  dna2bit    XyZabc456DefGh...         f7e8d9c0b1a2...
chrM     16569      dna2bit    MnOpQr789StUv...          1a2b3c4d5e6f...                   Mitochondrial DNA
```

The header line starts with `#` and defines column names.

**Data Columns:**

1. **name** (string): Sequence name (the first word from the FASTA header line)
2. **length** (integer): Sequence length in base pairs
3. **alphabet** (string): Alphabet type
   - `dna2bit`: 2-bit DNA encoding (ACGT only)
   - `dna3bit`: 3-bit DNA encoding (includes N)
   - `dnaio`: Full IUPAC DNA alphabet
   - `protein`: Protein sequences
   - `ASCII`: Generic ASCII sequences
4. **sha512t24u** (string): GA4GH SHA-512/24u digest (base64url, 32 chars)
   - Content-addressable identifier
   - Used as primary key for sequence lookup
5. **md5** (string): MD5 digest (hex, 32 chars)
   - Enables cross-referencing with MD5-based systems
6. **description** (string, optional): Text from the FASTA header after the first word
   - May be empty; trailing whitespace is stripped

Each sequence occupies one line, with lines starting with `#` serving as comments or headers. Fields are tab-separated and no quoting is required since sequence names cannot contain tabs.

### Sequence Files (.seq)

Individual sequence data files, one per sequence.

**Location:** Determined by `seqdata_path_template` in `rgstore.json`

**Naming:** Based on SHA-512/24u digest

**Format:** Binary

**Content depends on storage mode:** Raw mode stores plain sequence data as bytes (DNA as ASCII characters like A, C, G, T, N; protein as A, R, N, D, C, etc.) that is directly readable as text, while encoded mode uses bit-packed sequence data (DNA 2-bit packs 4 nucleotides per byte for ACGT; DNA 3-bit stores ~2.67 nucleotides per byte including N) that is more space-efficient but requires decoding to read. For example, human chr1 (248 Mbp) takes ~248 MB in raw mode but only ~62 MB in encoded 2-bit mode (4× compression).

### Collection Files (.rgsi)

Metadata files grouping sequences into collections (e.g., genome assemblies).

**Location:** `<store-root>/collections/<collection-digest>.rgsi`

**Format:** Tab-separated values (TSV) with header sections

**Structure:**
```
##seqcol_digest=uC_UorBNf3YUu1YIDainBhI94CedlNeH
##names_digest=zxcvbnmasdfghjkl
##sequences_digest=qwertyuiopasdfgh
##lengths_digest=poiuytrewqlkjhgf
##name_length_pairs_digest=abcdefghijklmnop
##sorted_name_length_pairs_digest=mnopqrstuvwxyzab
##sorted_sequences_digest=stuvwxyzabcdefgh
#name	length	alphabet	sha512t24u	md5	description
chr1	248956422	dna2bit	AbCdEf123GhIjK...	a1b2c3d4e5f6...	Homo sapiens chromosome 1
chr2	242193529	dna2bit	XyZabc456DefGh...	f7e8d9c0b1a2...
```

The header section uses `##` (double hash) for collection-level metadata headers. These include:

- `##seqcol_digest`: The GA4GH sequence collection digest (level 1 digest)
- `##names_digest`: Digest of the `names` array
- `##sequences_digest`: Digest of the `sequences` array
- `##lengths_digest`: Digest of the `lengths` array
- `##name_length_pairs_digest`: Digest of the `name_length_pairs` array
- `##sorted_name_length_pairs_digest`: Digest of the `sorted_name_length_pairs` array (coordinate system identifier)
- `##sorted_sequences_digest`: Digest of the `sorted_sequences` array

The data section header uses `#` (single hash) and is tab-separated.

**Data Section:**
Same format as `sequences.rgsi` (6 columns including `description`), but only the sequences in this collection.

### Alias Files (.tsv)

Alias files map human-readable names to sequence or collection digests, organized by namespace.

**Location:** `<store-root>/aliases/sequences/<namespace>.tsv` or `<store-root>/aliases/collections/<namespace>.tsv`

**Format:** Tab-separated values (TSV), two columns

**Schema:**
```
alias	digest
chr1	AbCdEf123GhIjKlMnOpQrStUvWxYzAb
NC_000001.11	AbCdEf123GhIjKlMnOpQrStUvWxYzAb
hg38	uC_UorBNf3YUu1YIDainBhI94CedlNeH
```

Each row maps one alias string (column 1) to one digest (column 2), tab-separated. No header line is used. Multiple aliases from different namespaces can point to the same digest.

**Namespace directories:**

- `aliases/sequences/` — contains one file per namespace for sequence aliases (e.g., `insdc.tsv`, `genbank.tsv`)
- `aliases/collections/` — contains one file per namespace for collection aliases (e.g., `ucsc.tsv`, `ncbi.tsv`)

### FHR Sidecar Files (.fhr.json)

FHR (FAIR Headers Reference genome) sidecar files attach structured metadata to a collection, following the [FHR specification](https://github.com/FAIR-bioHeaders/FHR-Specification).

**Location:** `<store-root>/collections/<collection-digest>.fhr.json`

**Format:** JSON

**Example:**
```json
{
  "schema_version": 1,
  "accessionID": {"id": "GCA_000001405.15", "source": "NCBI"},
  "taxon": [{"name": "Homo sapiens", "taxid": "9606"}],
  "description": "GRCh38 human reference genome",
  "scholarly_article": "https://doi.org/10.1038/nature15393",
  "funding": "National Human Genome Research Institute"
}
```

Each collection may have at most one `.fhr.json` sidecar. The sidecar is loaded automatically when the collection is opened, and an empty metadata object is stored if no sidecar file exists (zero-cost). See the [FHR specification](https://github.com/FAIR-bioHeaders/FHR-Specification) for the full field list.

## Storage Modes

RefgetStore supports two storage modes: **Raw mode** stores sequences as plain text (for DNA/protein), making them simple to debug and inspect with no decoding overhead, but results in larger file sizes without compression—use this when storage space is not a concern, you need human-readable sequences, or during debugging and development. **Encoded mode** provides 2-4× smaller file sizes through efficient bit-packing and faster I/O, though it requires decoding and is slightly more complex—use this for production deployments and storing large genomes where storage space matters.

For details on how RefgetStore's bit-packed encoding works and how it compares to the UCSC 2bit format, see [RefgetStore encoding](encoding-comparison.md).

## Path Templates

Templates use placeholders to organize files hierarchically:

### Sequence Path Templates

**Pattern:** `sequences/%s2/%s.seq`

Placeholders include `%s` (full 32-character digest), `%s2` (first 2 characters), and `%s4` (first 4 characters).

**Example:**
```
Digest: AbCdEf123GhIjKlMnOpQrStUvWxYzAb
Template: sequences/%s2/%s.seq
Result: sequences/Ab/AbCdEf123GhIjKlMnOpQrStUvWxYzAb.seq
```

Using digest prefixes prevents directories with millions of files, provides better filesystem performance, and cleaner organization. Common patterns include `sequences/%s2/%s.seq` (2-char prefix, 256 subdirectories), `sequences/%s4/%s.seq` (4-char prefix, 65,536 subdirectories), and `sequences/%s.seq` (flat structure, not recommended for large stores).

## Content-Addressable Storage

RefgetStore uses **content-addressable storage**: sequences are identified by their digest (hash of content), not by name.

### Benefits

Content-addressable storage enables **deduplication** by storing identical sequences only once, even when they appear in different assemblies (like chrM shared between GRCh38 and GRCh37). The digest-based approach ensures **integrity** by verifying that content hasn't been corrupted, providing tamper-evident storage. Finally, it creates **universal identifiers** where the same sequence has the same digest everywhere, enabling distributed, federated stores that are portable across systems.

### Example

```
GRCh38 chr1: sha512t24u = AbCdEf123...
GRCh37 chr1: sha512t24u = XyZabc456...  (different sequence)
GRCh38 chrM: sha512t24u = MnOpQr789...
GRCh37 chrM: sha512t24u = MnOpQr789...  (same sequence as GRCh38!)
```

Only 3 sequence files needed, even though we have 4 sequence references.

## GA4GH Compliance

RefgetStore implements the [GA4GH refget specification](https://samtools.github.io/hts-specs/refget.html), using SHA-512/24u digests (truncated SHA-512, base64url encoded) and supporting both Level 1 and Level 2 sequence collection digests.

## Using RefgetStore

For Python API usage (creating, loading, querying, and exporting), see the [RefgetStore tutorial](../using-services/refgetstore.py). For API reference documentation, see the [Python API reference](reference_docs.md#refgetstore-gtars).

## Distribution

### Local Distribution
Package the entire directory and distribute:
```bash
tar -czf refget-store.tar.gz /path/to/refget-store/
```

### Remote Distribution
Host on any static file server or object storage:
```bash
# S3
aws s3 sync /path/to/refget-store/ s3://bucket/refget-store/

# HTTP server
python -m http.server -d /path/to/refget-store/
```

Remote access provides lazy loading (only downloading sequences when requested), user-controlled caching (you specify where cached data is stored), bandwidth efficiency (only transferring needed data), and selective downloads (skipping sequences you don't need). See the [RefgetStore tutorial](../using-services/refgetstore.py) for Python API examples of connecting to remote stores.

## Cache Directory

When a remote store is accessed, a local cache directory mirrors the remote store structure. The cache location is user-specified (not automatic), giving explicit control over disk usage and placement.

The cache directory has the same on-disk layout as any RefgetStore:

- `rgstore.json` is re-downloaded on *every* connection, not just the first, so a client always evaluates the remote's current manifest. It is marked with a `.origin` file recording which remote URL it belongs to, so a cache directory cannot silently be reused against a different remote.
- `collections.rgci` and every alias namespace the manifest declares (`aliases/sequences/<ns>.tsv`, `aliases/collections/<ns>.tsv`) are fetched alongside the manifest. A cached index or alias file is only re-fetched when the manifest's corresponding digest (`collections_digest`, `aliases_digest`, ...) changes from what the cache last saw.
- `sequences.rgsi` is deferred: it is downloaded the first time a sequence operation actually needs it, not at connection time. For a large store this file reaches tens of megabytes, and browsing or listing collections does not need it. Use the manifest's `logical_sequence_bytes` to report the store's data size before the sequence index has been fetched.
- `sequences/` and `collections/` files are downloaded on-demand only when a specific sequence or collection is first accessed; cached `.seq` payloads are content-addressed by digest, so manifest changes never invalidate them.
- The cache can be shared between processes and is cleaned up by simply deleting the directory

See [How RefgetStore defers loading](../lazy-loading-explained.md) for the record-level and index-level deferral rules this layout supports.

## Design Rationale

### Why separate files per sequence?

Separate files per sequence enable selective memory mapping (mmap only the sequences you need, not an entire archive), automatic deduplication (identical sequences naturally share the same digest-named file), and simplified remote access (download only the specific sequence files you need with standard HTTP range requests). The key advantage over indexed single files is granular resource management—you can load, cache, and mmap individual sequences independently, which is particularly beneficial for distributed storage systems, content delivery networks, and partial synchronization where you don't want to handle a monolithic file.

### Why use digest prefixes in paths?

Digest prefixes avoid filesystem limits (directories with millions of files), improve directory lookup performance, and make it easier to shard across multiple servers or buckets.

### Why support both Raw and Encoded?

Supporting both modes provides flexibility to trade space for simplicity, with raw mode easier to debug during development and encoded mode providing efficiency for production.

### Why include MD5?

MD5 support provides compatibility with legacy systems, easier migration from MD5-based systems, and cross-referencing between old and new identifiers.

## See Also

- [GA4GH refget specification](https://samtools.github.io/hts-specs/refget.html)
- [RefgetStore encoding](encoding-comparison.md) — bit-packing details and comparison with UCSC 2bit
- [RefgetStore Python API](reference_docs.md#refgetstore-gtars)
- [RefgetStore tutorial](../using-services/refgetstore.py)
