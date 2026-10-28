# What is RefgetStore?

RefgetStore is a content-addressable sequence database that stores both individual sequences and sequence collections (like genome assemblies). It provides a local, file-based alternative to traditional sequence storage formats while supporting remote access and automatic caching.

At its core, **RefgetStore is a file format** — a directory layout for sequences and collections, addressed by their GA4GH refget digests. Around that format sits a stack of software (a Rust engine, language bindings, servers, and a web explorer) that all share the name "refget" or "RefgetStore." See [Components](#components) below for the full list with links.

## Local vs. remote RefgetStores

A RefgetStore is just a directory of files, so the same store can live in three places:

- **Local store** — a directory on your own disk. Fully self-contained; read and write it with no server and no network.
- **Remote store** — the identical directory layout hosted on static object storage (S3) or any HTTP file server. Because access is content-addressable and range-based, **no application server is required** — a plain bucket is enough to serve sequences.
- **Local cache of a remote store** — point a local store at a remote URL. Sequences are downloaded on demand and cached locally; subsequent requests are served from the cache. You get remote breadth with local speed.

This local/remote symmetry is the defining feature: the *same* store works on a laptop, on S3, or as a cache bridging the two.

## Why use RefgetStore?

Existing sequence formats are optimized for different use cases:

| Format | Strengths | Gaps |
|--------|-----------|------|
| FASTA + .fai | Universal, indexed random access | No deduplication, no collection tracking |
| bgzip + index | Compressed with random access | No deduplication, no collection tracking |
| 2bit | Compact, fast access | DNA only, no collection tracking |
| seqrepo | Content-addressable, deduplication, namespaces | Requires SQLite, no collection tracking |

RefgetStore is most similar to [seqrepo](https://github.com/biocommons/biocommons.seqrepo). Both provide content-addressable storage with deduplication. RefgetStore differs in being purely file-based (no database), supporting static file hosting (S3, HTTP) without a server, native support for GA4GH sequence collections, and adaptive encoding that provides smaller files with faster random access.

## Key features

### Collection management

Unlike formats that only store sequences, RefgetStore tracks sequence collections (genome assemblies, transcriptomes, etc.). You can query by collection digest and retrieve sequences by their local names within that collection.

### Universal identifiers

Every sequence and collection has a GA4GH refget digest. This enables:

- Reproducible retrieval by content hash
- Lookup by digest alone, or by (collection digest + sequence name)
- Computing derived digests (name/length pairs) for coordinate system comparison

### Automatic deduplication

Identical sequences are stored once, even across different assemblies. For example, mitochondrial sequences are often identical between GRCh38 and GRCh37—RefgetStore stores them once and references them from both collections.

### Efficient encoding

RefgetStore automatically selects the optimal encoding for each sequence:

| Alphabet | Encoding |
|----------|----------|
| DNA (ACGT only) | 2-bit |
| DNA with N, R, Y (other characters become X) | 3-bit |
| DNA with full IUPAC ambiguity codes | 4-bit |
| Protein (amino acids, stop codons, gaps) | 5-bit |
| Anything else (ASCII fallback) | 8-bit |

This provides compression while maintaining fast random access—no decompression needed.

### Remote access with caching

Connect a local store to a remote URL (HTTP, S3, or any file server). Sequences are downloaded on-demand and cached locally. Subsequent requests are served from the local cache.

### Region extraction

Extract subsequences by coordinates. Batch extraction from BED files is optimized for high throughput.

### File-based simplicity

No database server required. A RefgetStore is just a directory structure that can be:

- Copied and backed up with standard tools
- Hosted on any static file server
- Inspected directly on disk

## Components

The RefgetStore name spans the storage format *and* the layers of software built on top of it. Here are the pieces, from the bytes on disk up to the website you click on.

### The format

The RefgetStore format is the on-disk (or on-S3) directory layout itself — sequences and collections addressed by their digests. See the [format reference](reference/refgetstore-format.md).

### The engine (Rust)

[**`gtars`**](https://github.com/databio/gtars) is the Rust project at the heart of everything here. The RefgetStore implementation lives in its [`gtars-refget`](https://github.com/databio/gtars/tree/master/gtars-refget) crate ([crates.io](https://crates.io/crates/gtars-refget)), which reads and writes stores — local and remote/S3, with adaptive encoding and deduplication. Every component below is ultimately a wrapper around this engine.

### Bindings

The Rust engine is exposed to four other languages, all built from the same [`gtars`](https://github.com/databio/gtars) repo:

| Language | Package | Where |
|----------|---------|-------|
| Python | `gtars` | [GitHub](https://github.com/databio/gtars/tree/master/gtars-python) · [PyPI](https://pypi.org/project/gtars/) |
| Node.js | `@databio/gtars-node` | [GitHub](https://github.com/databio/gtars/tree/master/gtars-node) · [npm](https://www.npmjs.com/package/@databio/gtars-node) |
| WebAssembly | `@databio/gtars` | [GitHub](https://github.com/databio/gtars/tree/master/gtars-wasm) · [npm](https://www.npmjs.com/package/@databio/gtars) |
| R | `gtars` (R package) | [GitHub](https://github.com/databio/gtars/tree/master/gtars-r) |

The WebAssembly build exposes only the digest/encoding subset (the WASM-safe parts) for in-browser use; the others expose the full `RefgetStore` API.

### High-level library

[**`refget`**](https://github.com/refgenie/refget) ([PyPI](https://pypi.org/project/refget/)) is the friendly Python package most users start with. It wraps the store and adds clients, database agents, a FastAPI router, and a CLI.

### Servers

Two servers put a RefgetStore (or other backend) behind the GA4GH HTTP APIs — each focused on a different half of the standard:

| Server | What it is | Where |
|--------|------------|-------|
| `seqcolapi` | A Python/FastAPI implementation of the GA4GH **Sequence Collections API** (collection metadata + comparison). Part of the `refget` package; backed by PostgreSQL or a RefgetStore. | [GitHub](https://github.com/refgenie/refget/tree/master/seqcolapi) · live: [seqcolapi.databio.org](https://seqcolapi.databio.org) |
| `refgetstore-server` | A demo of the GA4GH **Refget Sequences API** (retrieve sequence residues by digest), served straight from a RefgetStore with no database. Node.js, built on the [`@databio/gtars-node`](https://www.npmjs.com/package/@databio/gtars-node) bindings. | [GitHub](https://github.com/databio/refgetstore-node-demo) |

They cover complementary halves of the API — see [How the pieces fit together](#how-the-pieces-fit-together) below.

### Web explorer

The [**refget explorer**](https://refget.databio.org/explore) is a React app for browsing collections and stores in the browser ([source](https://github.com/refgenie/refget/tree/master/frontend)).

### How the pieces fit together

These components are designed to combine into a complete service. In a typical deployment, sequences and collections live in a RefgetStore on S3, and the two servers handle complementary halves of the GA4GH API on top of it: `seqcolapi` answers questions *about* collections (their names, lengths, and digests, and how two collections compare), while `refgetstore-server` serves the sequence residues themselves. The explorer web app sits in front, calling `seqcolapi` so users can browse and compare collections in the browser.

Because a RefgetStore is static and content-addressable, you can also serve sequence bytes straight from the S3 bucket with no server at all — `refgetstore-server` is what you add when you want streaming and on-the-fly decoding of encoded stores.

## Learn more

- [Getting started tutorial](using-services/getting-started.py) - Quick introduction to computing digests
- [RefgetStore tutorial](using-services/refgetstore.py) - Hands-on guide to using RefgetStore
- [How RefgetStore defers loading](lazy-loading-explained.md) - Why opening a store is cheap, and what gets fetched when
- [The readonly store and concurrency](readonly-store-explained.md) - Sharing a store across threads in a server
- [How FASTA import works](fasta-import-explained.md) - The import pipeline and the digest cache
- [RefgetStore file format](reference/refgetstore-format.md) - Technical specification of the directory structure
- [CLI reference](reference/cli.md) - Command-line interface for RefgetStore operations
- [Names, aliases, and identifiers](names-and-aliases-explained.md) - How human-readable registry identifiers work alongside digests and sequence names
- [Understanding FHR metadata](fhr-metadata-explained.md) - How to attach structured assembly-level metadata to collections
- [The reference genome jungle](genome-collections-explained.md) - A public RefgetStore of human and mouse reference assemblies from many providers
- [Browse live collections](https://refget.databio.org/explore) - The public RefgetStore explorer

**See also:** RefgetStore is implemented in the Rust crate [gtars-refget](https://docs.bedbase.org/gtars/refget/). The gtars docs cover the Rust API and its bindings: [Python RefgetStore reference](https://docs.bedbase.org/gtars/python/refget-store/) and [R RefgetStore](https://docs.bedbase.org/gtars/r/refgetstore/).
