# Refget CLI Reference

The `refget` command-line interface provides tools for working with reference sequences following GA4GH standards. It includes commands for computing sequence collection digests, managing local sequence stores, and interacting with remote seqcol APIs.

## Installation

```bash
pip install refget
```

## Quick Start

```bash
# Compute seqcol digest from a FASTA file
refget fasta digest genome.fa

# Create all index files from a FASTA
refget fasta index genome.fa

# Initialize a local sequence store
refget store init

# Add a FASTA to the store
refget store add genome.fa

# Compare two sequence collections
refget seqcol compare genome1.fa genome2.fa
```

## Command Groups

The CLI is organized into five command groups:

| Group | Description |
|-------|-------------|
| `refget config` | Configuration management |
| `refget fasta` | FASTA file utilities |
| `refget store` | RefgetStore operations |
| `refget seqcol` | Sequence collection API |
| `refget admin` | Admin/database operations |

---

## Global Options

```
--version, -v    Show version and exit
--help           Show help message and exit
```

---

## Config Commands

Manage refget configuration stored in `~/.refget/config.toml`.

### config init

Interactive setup wizard for refget configuration.

```bash
refget config init [--force]
```

**Options:**

- `--force, -f`: Overwrite existing configuration

### config show

View all configuration or a specific section.

```bash
refget config show [SECTION]
```

**Arguments:**

- `SECTION`: Optional section to show (store, seqcol_servers, remote_stores, admin)

### config get

Get a specific configuration value.

```bash
refget config get KEY
```

**Examples:**
```bash
refget config get store.path
refget config get admin.postgres_host
```

### config set

Set a configuration value.

```bash
refget config set KEY VALUE
```

**Examples:**
```bash
refget config set store.path /path/to/store
refget config set admin.postgres_host localhost
```

### config path

Show the path to the configuration file.

```bash
refget config path
```

### config validate

Validate the configuration file.

```bash
refget config validate
```

### config add

Add a server or store to the configuration.

```bash
refget config add RESOURCE_TYPE URL [--name NAME]
```

**Arguments:**

- `RESOURCE_TYPE`: One of: `seqcol_server`, `remote_store`, or `sequence_server`
- `URL`: URL of the server/store to add

**Options:**

- `--name, -n`: Optional name for this server/store

**Examples:**
```bash
refget config add seqcol_server https://seqcolapi.databio.org --name databio
refget config add remote_store s3://bucket/store/ --name primary
refget config add sequence_server https://www.ebi.ac.uk/ena/cram/ --name ebi
```

### config remove

Remove a server or store from the configuration.

```bash
refget config remove RESOURCE_TYPE NAME
```

**Examples:**
```bash
refget config remove seqcol_server databio
refget config remove remote_store primary
```

---

## FASTA Commands

Utilities for processing FASTA files and computing seqcol data.

### fasta digest

Compute the seqcol digest (top-level) of a FASTA file.

```bash
refget fasta digest FILE
```

**Output:** JSON with digest and file path
```json
{"digest": "abc123...", "file": "genome.fa"}
```

### fasta seqcol

Compute the full seqcol JSON from a FASTA file.

```bash
refget fasta seqcol FILE [-o OUTPUT] [-l LEVEL]
```

**Options:**

- `--output, -o`: Output file path (default: stdout)
- `--level, -l`: Seqcol level: 1 (digests only) or 2 (full arrays). Default: 2

**Example:**
```bash
refget fasta seqcol genome.fa -o genome.seqcol.json
```

### fasta index

Generate ALL derived files from a FASTA file.

```bash
refget fasta index FILE [-o OUTPUT_DIR] [--json]
```

For `genome.fa`, creates:

- `genome.fa.fai` - FASTA index (samtools-compatible)
- `genome.seqcol.json` - Sequence collection JSON
- `genome.chrom.sizes` - Chromosome sizes

**Options:**

- `--output-dir, -o`: Output directory (default: same as input file)
- `--json, -j`: Output result as JSON

### fasta fai

Compute FAI index from a FASTA file.

```bash
refget fasta fai FILE [-o OUTPUT]
```

Outputs samtools-compatible .fai format (tab-separated).

### fasta chrom-sizes

Compute chrom.sizes from a FASTA file.

```bash
refget fasta chrom-sizes FILE [-o OUTPUT]
```

Outputs UCSC-compatible chrom.sizes format (tab-separated name/length).

### fasta stats

Display statistics for a FASTA file.

```bash
refget fasta stats FILE [--json]
```

Shows: sequence count, total length, N50, min/max/mean sequence length.

**Options:**

- `--json, -j`: Output as JSON instead of table

### fasta validate

Validate a FASTA file format.

```bash
refget fasta validate FILE
```

Returns exit code 0 if valid, non-zero if invalid.

### fasta rgsi

Compute .rgsi (RefgetStore sequence index) from a FASTA file.

```bash
refget fasta rgsi FILE [-o OUTPUT]
```

The .rgsi file contains sequence metadata in RefgetStore format.

### fasta rgci

Compute .rgci (RefgetStore collection index) from a FASTA file.

```bash
refget fasta rgci FILE [-o OUTPUT]
```

The .rgci file contains collection metadata in RefgetStore format.

---

## Store Commands

Manage a local RefgetStore for storing and retrieving sequences. See [What is RefgetStore?](../refgetstore-explained.md) for the concepts and [RefgetStore file format](refgetstore-format.md) for the on-disk layout. The direct store subcommands are `init`, `add`, `list`, `match`, `get`, `pull`, `export`, `regions`, `chrom-sizes`, `stats`, `remove`, `crate`, `explore`, and `serve`, plus the `alias` and `fhr` command groups documented below. Most commands accept `--path PATH` to select a local store (default: from config); where noted, they also accept `--remote URL` to read directly from a remote store instead.

### store init

Initialize a local RefgetStore.

```bash
refget store init [--path PATH]
```

**Options:**

- `--path, -p`: Path for the store (default: from config or `~/.refget/store`)

### store add

Import one or more FASTA files into the local store.

```bash
refget store add FASTAS... [--namespace NS ...] [--file-list FILE] [--jobs N] [--force] [--path PATH] [--mode MODE] [--quiet]
```

Accepts explicit paths, glob patterns, and directories (expanded by gtars), plus a file-of-filenames via `--file-list`. Creates a sequence collection from each FASTA and stores all of its sequences; identical sequence content is deduplicated across files and collections.

**Arguments:**

- `FASTAS...`: FASTA paths, glob patterns, or directories to import (supports `.gz`). Can be omitted if `--file-list` supplies the inputs instead.

**Options:**

- `--namespace, -N`: Namespace prefix to extract aliases from FASTA headers (repeatable), e.g. `-N ucsc -N refseq`
- `--file-list, -F`: File-of-filenames (one path/glob/directory per line)
- `--jobs, -j`: Concurrent imports (`0` = auto, `1` = serial; default `0`)
- `--force, -f`: Overwrite existing collections/sequences
- `--path, -p`: Store path (default: from config)
- `--mode, -m`: Storage mode override: `encoded` (compressed, ~4x smaller, default) or `raw` (faster access, easier to inspect). Set at add time rather than at `init`, since mode describes how sequences are encoded and an empty store has no sequences yet.
- `--quiet, -q`: Suppress progress output

**Output:** a single explicit path returns one object; multiple inputs (globs, `--file-list`, or `--jobs` > 1) return a batch report instead. The batch report's `n_*` fields are per-run ingest counters -- use them (not `store stats`) to report what an `add` run actually did.

Single explicit path:
```json
{"digest": "abc123...", "fasta": "genome.fa", "sequences": 25, "was_new": true}
```

Multiple inputs:
```json
{
  "results": [
    {"digest": "IhtTMDzhGDWFvmoXdLg4KwcslTzDtPaO", "sequences": 1, "was_new": true},
    {"digest": "kd2A0MKmZCwr9SH8IM5MNYioSUVcVMfD", "sequences": 1, "was_new": true}
  ],
  "count": 2,
  "n_sequences_written": 2,
  "n_sequences_deduped": 0,
  "n_collections_new": 2
}
```

**Examples:**
```bash
refget store add genome.fa
refget store add 'fastas/*.fa.gz' --jobs 4
refget store add --file-list manifest.txt
refget store add dir1/ dir2/ -N ucsc
```

### store list

Browse collections, the chromosome or contig names within one collection, or
the store's global deduplicated sequence records.

```bash
refget store list [COLLECTION] [--sequences] [--path PATH] [--remote URL]
```

**Arguments:**

- `COLLECTION`: Optional collection digest or `NAMESPACE:ALIAS`, such as
  `ucsc:hg38`. When provided, the command lists that collection's own sequence
  names in original FASTA order.

**Options:**

- `--sequences, -s`: List globally deduplicated sequence records instead of
  collections. This cannot be combined with `COLLECTION`.
- `--path, -p`: Store path (default: from config)
- `--remote, -r`: Remote store URL (overrides --path)

Without an argument, the command returns all collections, including sequence
counts and registered collection aliases:

```json
{
  "collections": [
    {
      "digest": "abc123...",
      "n_sequences": 455,
      "aliases": [["ucsc", "hg38"]]
    }
  ]
}
```

With a collection selector, it returns collection identity plus its
collection-local names, lengths, and canonical sequence identifiers:

```json
{
  "collection": {
    "digest": "abc123...",
    "n_sequences": 455,
    "aliases": [["ucsc", "hg38"]]
  },
  "sequences": [
    {"name": "chr1", "length": 248956422, "digest": "xyz..."}
  ]
}
```

Every row -- collection-local names, the global sequence inventory, and match results below -- identifies a sequence by the bare `digest` field: the sha512t24u value with no `SQ.` prefix. (The `SQ.`-prefixed form only appears in the GA4GH-spec `sequences` array returned by `store get`, which follows the seqcol Level 2 wire format rather than this CLI's row schema.)

`--sequences` retains the separate global sequence-store view:

```json
{"sequences": [{"digest": "abc123...", "name": "chr1", "length": 12345}, ...]}
```

Collection-local names and global sequence records are deliberately different:
identical sequence content is stored once globally but may be named `chr1`,
`1`, or another label in different collections.

**Examples:**

```bash
# Inventory of collections and aliases
refget store list --path /data/refget

# Chromosomes/contigs for a collection selected by alias or digest
refget store list ucsc:hg38 --path /data/refget
refget store list abc123... --path /data/refget

# Global deduplicated sequence records
refget store list --sequences --path /data/refget
```

### store match

Translate chromosome or contig names between two stored collections by joining
their collection-local records on canonical sequence digest. Selectors may be
collection digests, collection aliases, or one of each.

```bash
refget store match COLLECTION_A COLLECTION_B [--include-unmatched] [--path PATH] [--remote URL]
```

**Arguments:**

- `COLLECTION_A`: First collection digest or `NAMESPACE:ALIAS`.
- `COLLECTION_B`: Second collection digest or `NAMESPACE:ALIAS`.

**Options:**

- `--include-unmatched`: Include sequences present in only one collection.
- `--path, -p`: Store path (default: from config).
- `--remote, -r`: Remote store URL (overrides `--path`).

Each matched group contains the shared bare sequence `digest` (sha512t24u,
no `SQ.` prefix) and length plus every name used for that content in each
collection. Name arrays make one-to-many relationships explicit rather than
arbitrarily choosing one label.

```json
{
  "collection_a": "digest-a...",
  "collection_b": "digest-b...",
  "matches": [
    {
      "digest": "xyz...",
      "length": 23513712,
      "names_a": ["chr2L"],
      "names_b": ["2L"]
    }
  ]
}
```

With `--include-unmatched`, the response also includes `a_only` and `b_only`
arrays with the same row structure -- each entry has an empty `names_a` or
`names_b` for the collection that lacks the sequence.

**Examples:**

```bash
# Match two named collections
refget store match ucsc:dm6 flybase:r6.68 --path /data/refget

# Match by digest and retain sequences found on only one side
refget store match digest-a... digest-b... \
  --include-unmatched --path /data/refget

# Match against a remote store without pulling it locally first
refget store match ucsc:dm6 flybase:r6.68 --remote https://example.com/store
```

### store get

Get a collection or sequence by digest.

```bash
refget store get DIGEST [--sequence] [--name NAME] [--start N] [--end M] [--path PATH] [--remote URL]
```

**Options:**

- `--sequence, -s`: Get a sequence instead of a collection
- `--name, -n`: Get sequence by name from a collection (requires collection digest)
- `--start`: Subsequence start position (0-based)
- `--end`: Subsequence end position (exclusive)
- `--path, -p`: Store path (default: from config)
- `--remote, -r`: Remote store URL (overrides --path)

**Output:** Full seqcol JSON (default), or raw sequence string with `--sequence` or `--name`.

**Examples:**
```bash
# Get collection by digest
refget store get abc123

# Get sequence by digest
refget store get <seq_digest> --sequence

# Get sequence by name from collection
refget store get <coll_digest> --name chr1

# Get subsequence
refget store get <seq_digest> --sequence --start 100 --end 200

# Get from remote store
refget store get abc123 --remote https://example.com/store
```

**Note:** Digests with `SQ.` prefix (e.g., `SQ.abc123`) are automatically normalized—the prefix is stripped before lookup.

### store pull

Pull collections from a remote store into the local store.

```bash
refget store pull [DIGEST] [--file FILE] [--remote URL] [--path PATH] [--alias-strategy STRATEGY] [--quiet]
```

Each requested collection is imported in full: sequences, aliases, and FHR metadata are all materialized into the local on-disk store. There is no lazy pull mode -- for on-demand access to a remote store without copying it locally, open it with `--remote` on the read commands instead. Before importing, the remote's alias and FHR sidecars are fetched (using `--alias-strategy` to resolve conflicts) so they travel with the collection.

**Arguments:**

- `DIGEST`: Collection digest to pull. Omit when using `--file` for a batch pull.

**Options:**

- `--file, -f`: File containing digests (one per line) for batch pull
- `--path, -p`: Local store path (default: from config)
- `--remote, --server, -r`: Remote store URL. If omitted, resolution tries, in order: (1) the local store, (2) configured `remote_stores`, then (3) configured `seqcol_servers` (discovered via service-info).
- `--alias-strategy`: Conflict strategy when fetching alias/FHR sidecars from the remote: `keep-ours`, `keep-theirs`, or `notify` (default: `keep-ours`)
- `--quiet, -q`: Suppress progress output

**Examples:**
```bash
refget store pull ABC123 --remote https://example.com/store
refget store pull --file digests.txt --remote https://example.com/store
```

### store export

Export sequences as a FASTA file, in one of four modes.

```bash
refget store export [DIGEST] [-o OUTPUT] [--bed BED] [--name NAME] [--seq-digest DIGEST] [--path PATH] [--remote URL] [--line-width N]
```

**Modes** (pick one):

- Full collection: `DIGEST` alone
- Subset by names: `DIGEST --name chr1 --name chr2`
- Regions from a BED file: `DIGEST --bed regions.bed`
- Ad-hoc by *sequence* digest, bypassing collections entirely: `--seq-digest SEQ_DIGEST` (repeatable). This mode takes sequence digests, not a collection digest, and ignores the `DIGEST` argument if one is given.

**Options:**

- `--output, -o`: Output FASTA file path (default: stdout)
- `--bed, -b`: BED file for region extraction
- `--name, -n`: Sequence names to include (repeatable)
- `--seq-digest, -S`: Export ad-hoc by sequence digest, bypassing collections (repeatable; see modes above)
- `--path, -p`: Store path (default: from config)
- `--remote, -r`: Remote store URL (overrides `--path`)
- `--line-width, -w`: FASTA line width (default: 80)

**Examples:**
```bash
# Export full collection
refget store export abc123 -o genome.fa

# Export specific chromosomes
refget store export abc123 -o subset.fa --name chr1 --name chr2

# Export regions from BED file
refget store export abc123 -o regions.fa --bed regions.bed

# Export by sequence digest, bypassing collections
refget store export --seq-digest xyz123... --seq-digest xyz456... -o seqs.fa
```

### store regions

Extract BED-file regions from a collection as structured sequence data. Local- and remote-capable.

```bash
refget store regions DIGEST --bed BED [--json] [--path PATH] [--remote URL]
```

Reads a BED file and returns the sequence for each region. By default, emits FASTA-style records with headers `>{chrom}:{start}-{end}`; `--json` emits a list of `{chrom_name, start, end, sequence}` objects instead. Unlike `store export --bed`, which writes a FASTA file, `regions` is the structured/JSON-friendly form of the same extraction.

**Arguments:**

- `DIGEST` (required): Collection digest to extract regions from

**Options:**

- `--bed, -b` (required): BED file of regions to extract
- `--json, -j`: Output as a JSON list of region records instead of FASTA
- `--path, -p`: Store path (default: from config)
- `--remote, -r`: Remote store URL (overrides `--path`)

**Example:**
```bash
refget store regions abc123 --bed regions.bed
refget store regions abc123 -b regions.bed --json
```
```json
[{"chrom_name": "chr1", "start": 0, "end": 5, "sequence": "ACGTA"}]
```

### store chrom-sizes

Generate chrom.sizes from a collection digest. Local- and remote-capable.

```bash
refget store chrom-sizes DIGEST [-o OUTPUT] [--path PATH] [--remote URL]
```

Outputs UCSC-compatible chrom.sizes format (tab-separated name/length).

**Options:**

- `--output, -o`: Output file path (default: stdout)
- `--path, -p`: Store path (default: from config)
- `--remote, -r`: Remote store URL (overrides `--path`)

### store stats

Display store statistics. Local- and remote-capable.

```bash
refget store stats [--path PATH] [--remote URL]
```

**Options:**

- `--path, -p`: Store path (default: from config)
- `--remote, -r`: Remote store URL (overrides `--path`)

**Output:** the store's stats dict. All values are emitted as JSON strings, not numbers or booleans:

- `n_sequences`: total number of sequences (Stub + Full)
- `n_sequences_in_memory`: number of sequences whose bytes are currently held in RAM (Full). This is a live RAM-residency gauge, not an ingest count -- it reads `"0"` for a store you just opened, since opening only reads metadata.
- `n_collections`: total number of collections (Stub + Full)
- `n_collections_in_memory`: number of collections whose sequence list is currently loaded in RAM. Also a residency gauge; it resets on process start and counts collections merely touched by a read, not collections ingested.
- `storage_mode`: `"Encoded"` or `"Raw"`
- `logical_sequence_bytes`: the logical encoded size of all sequence payloads, computed from sequence lengths and storage mode at index-write time. It excludes indexes, aliases, FHR sidecars, the manifest, and filesystem overhead, so it approximates but is not the exact on-disk footprint. See [RefgetStore file format](refgetstore-format.md).

For what a specific `add` run actually wrote, use that command's own output (`n_sequences_written`, `n_sequences_deduped`, `n_collections_new`) rather than `stats`, which is a snapshot of current state.

**Example output:**
```json
{
  "n_sequences": "3",
  "n_sequences_in_memory": "0",
  "n_collections": "2",
  "n_collections_in_memory": "0",
  "storage_mode": "Encoded",
  "logical_sequence_bytes": "25"
}
```

### store remove

Remove a collection from the store.

```bash
refget store remove DIGEST [--path PATH]
```

This removes the collection from the store's index. Associated sequences are not removed, since they may be shared with other collections.

**Options:**

- `--path, -p`: Store path (default: from config)

### store crate

Generate an RO-Crate metadata file describing the store as a FAIR research object -- structure, provenance, and statistics. Local-only.

```bash
refget store crate --name NAME [--path PATH] [--description TEXT] [--author "Name <URL>"] [--license URL] [-o OUTPUT]
```

Writes `ro-crate-metadata.json` (or the path given by `--output`) conforming to the [RO-Crate](https://www.researchobject.org/ro-crate/) specification. The store's own `store crate` command is the canonical way to produce this file; see the [RO-Crate profile](https://w3id.org/ga4gh/refget/refgetstore-crate/0.1) it targets.

**Options:**

- `--path, -p`: Store path (default: from config)
- `--name, -n` (required): Name for the RO-Crate root dataset
- `--description, -d`: Description of the store
- `--author, -a`: Author, in `"Name <URL>"` format, e.g. `"Jane Doe <https://orcid.org/...>"`
- `--license, -l`: License URL
- `--output, -o`: Output path (default: `<store-path>/ro-crate-metadata.json`)

**Example:**
```bash
refget store crate --path /store --name "My genomes" --author "J Doe <https://orcid.org/0000-0001-1234-5678>"
```
```json
{"output": "/store/ro-crate-metadata.json", "status": "created", "entities": 14}
```

### store explore

Browse a local RefgetStore in your web browser -- no backend, no internet connection required. Local-only, read-only.

```bash
refget store explore [PATH] [--host HOST] [--port N] [--no-browser] [--frontend-dir DIR] [--store-only]
```

Serves the store's static files and the bundled Store Explorer single-page app from one localhost origin (so no CORS is involved), then opens the Explorer pointed at that store. Only `GET`/`HEAD` are served; no write or control operation is exposed -- use `store pull`/`add`/`alias` to modify a store. Unlike most store commands, `explore` doesn't require `gtars`; it's pure static file serving, so it also works against read-only CVMFS mounts and air-gapped servers.

**Arguments:**

- `PATH`: Local store directory to explore (default: from config)

**Options:**

- `--host`: Host/interface to bind (default: `127.0.0.1`)
- `--port, -P`: Port to serve on, auto-increments if busy (default: `8080`)
- `--no-browser`: Do not open a web browser; just print the URLs
- `--frontend-dir`: Override the Store Explorer SPA build directory
- `--store-only`: Serve only the store files (skip the SPA), for a self-hosted UI

**Examples:**
```bash
refget store explore /path/to/refget-store
refget store explore --no-browser --port 9000
```

### store serve

Serve a seqcol API backed by a RefgetStore. No database required. See [How to serve a RefgetStore concurrently](../hosting-services/howto-serve-refgetstore.md) for the full deployment recipe.

```bash
refget store serve [--path PATH | --remote URL] [--port N] [--host HOST] [--lazy]
```

By default the store is fully loaded and converted to a `ReadonlyRefgetStore`, whose read methods borrow immutably and are safe to share across request threads for concurrent serving. Pass `--lazy` to skip that load-and-convert step and serve directly from the mutable, lazy-loading store instead -- this avoids loading the whole store into memory up front, but is single-reader-oriented and **not** recommended for concurrent production serving. `explore` and `serve` are not interchangeable: `explore` is static, read-only browsing with no API; `serve` runs the actual seqcol HTTP API.

**Options:**

- `--path, -p`: Local store path
- `--remote, -r`: Remote store URL (e.g. `s3://bucket/store/`)
- `--port`: Port to serve on (default: `8000`)
- `--host`: Host to bind to; use `0.0.0.0` to expose on your network (default: `127.0.0.1`)
- `--lazy`: Serve from the mutable, lazy-loading store instead of converting to readonly

**Examples:**
```bash
refget store serve --path /path/to/store --port 8000
refget store serve --remote s3://bucket/store/ --port 8000
refget store serve --path /path/to/store --lazy
```

### store alias

Manage sequence and collection aliases -- human-readable `namespace:alias` names that resolve to a digest. See [Names, aliases, and identifiers](../names-and-aliases-explained.md) for the concepts.

```bash
refget store alias {add|get|list|rm|load|for} ...
```

All six actions operate on **collection** aliases by default; pass `--seq` to operate on sequence aliases instead. `add`, `rm`, and `load` are local-only writes. `get`, `list`, and `for` are reads that also accept `--remote URL`.

| Action | Usage | Notes |
|--------|-------|-------|
| `add` | `refget store alias add NAMESPACE ALIAS DIGEST [--seq] [--path PATH]` | Map `namespace:alias -> digest` |
| `get` | `refget store alias get NAMESPACE ALIAS [--seq] [--metadata] [--path PATH] [--remote URL]` | Resolve to a digest, or full metadata with `--metadata` |
| `list` | `refget store alias list [NAMESPACE] [--seq] [--namespaces] [--path PATH] [--remote URL]` | Omit `NAMESPACE` (or pass `--namespaces`) to list namespaces; give one to list its aliases |
| `rm` | `refget store alias rm NAMESPACE ALIAS [--seq] [--path PATH]` | Remove one alias |
| `load` | `refget store alias load NAMESPACE FILE [--seq] [--path PATH]` | Bulk-load `alias<TAB>digest` lines from a TSV file into a namespace |
| `for` | `refget store alias for DIGEST [--seq] [--path PATH] [--remote URL]` | Reverse lookup: every `(namespace, alias)` pair for a digest |

**Forward-lookup example:**
```bash
refget store alias add ucsc hg38 abc123...
refget store alias get ucsc hg38
```
```json
{"namespace": "ucsc", "alias": "hg38", "digest": "abc123...", "kind": "collection"}
```

**Reverse-lookup example:**
```bash
refget store alias for abc123...
```
```json
{"digest": "abc123...", "aliases": [["ucsc", "hg38"], ["ncbi", "GRCh38"]]}
```

### store fhr

Manage FHR (FAIR Headers Reference genome) metadata attached to a collection. See [Understanding FHR metadata](../fhr-metadata-explained.md) for the field meanings.

```bash
refget store fhr {get|set|set-fields|rm|list} ...
```

`get` and `list` are reads that also accept `--remote URL`. `set`, `set-fields`, and `rm` are local-only writes.

| Action | Usage | Notes |
|--------|-------|-------|
| `get` | `refget store fhr get DIGEST [--path PATH] [--remote URL]` | Show FHR metadata for a collection |
| `set` | `refget store fhr set DIGEST FILE [--path PATH]` | Set FHR metadata from a JSON file, replacing any existing metadata |
| `set-fields` | `refget store fhr set-fields DIGEST [FIELDS...] [--path PATH]` | Set FHR metadata from individual field options (below) |
| `rm` | `refget store fhr rm DIGEST [--path PATH]` | Remove FHR metadata for a collection |
| `list` | `refget store fhr list [--path PATH] [--remote URL]` | List collection digests that have FHR metadata |

`set-fields` accepts these field options; `--genome-synonym` and `--identifier` are repeatable, the rest are scalar:

`--genome`, `--version`, `--masking`, `--genome-synonym` (repeatable), `--voucher-specimen`, `--documentation`, `--identifier` (repeatable), `--scholarly-article`, `--funding`

**JSON-file example:**
```bash
refget store fhr set abc123... fhr_metadata.json
refget store fhr get abc123...
```

**Field-based example:**
```bash
refget store fhr set-fields abc123... --genome "Homo sapiens" --version GRCh38 \
  --genome-synonym hg38 --genome-synonym GRCh38.p14
```
```json
{"digest": "abc123...", "status": "set"}
```

---

## Seqcol Commands

Work with sequence collections and the seqcol API.

### seqcol compare

Compare two sequence collections.

```bash
refget seqcol compare A B [--server URL] [--quiet]
```

Accepts flexible inputs:

- `<digest>` - Fetches from local store or server
- `<file.fa>` - Computes seqcol on the fly
- `<file.seqcol.json>` - Uses local seqcol file

**Options:**

- `--server, -s`: Server URL override
- `--quiet, -q`: Suppress output; use exit code only (0=compatible, 1=incompatible)

**Example:**
```bash
refget seqcol compare genome1.fa genome2.fa
refget seqcol compare abc123 def456 --server https://seqcolapi.databio.org
```

### seqcol digest

Compute the seqcol digest of a file.

```bash
refget seqcol digest FILE
```

Accepts either a FASTA file or a `.seqcol.json` file.

### seqcol validate

Validate a seqcol JSON file.

```bash
refget seqcol validate FILE
```

Checks that the file is valid JSON and conforms to the seqcol schema.

### seqcol attributes

List attributes in a seqcol JSON file.

```bash
refget seqcol attributes FILE
```

Shows the attribute names and their array lengths.

### seqcol schema

Show the seqcol schema definition.

```bash
refget seqcol schema
```

### seqcol servers

List known seqcol servers from configuration.

```bash
refget seqcol servers
```

### seqcol show

Get a sequence collection by digest from local store or remote server.

```bash
refget seqcol show DIGEST [--level LEVEL] [--server URL]
```

Resolution order: local store -> configured seqcol_servers -> `--server` override

**Options:**

- `--level, -l`: Seqcol level: 1 (digests only) or 2 (full arrays). Default: 2
- `--server, -s`: Server URL override

**Examples:**
```bash
refget seqcol show XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk
refget seqcol show XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk --level 1
refget seqcol show XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk --server https://seqcolapi.databio.org
```

### seqcol list

List collections available on the server.

```bash
refget seqcol list [--server URL] [--limit N] [--offset N]
```

**Options:**

- `--server, -s`: Server URL override
- `--limit, -n`: Maximum number of collections to return (default: 100)
- `--offset`: Offset for pagination (default: 0)

### seqcol search

Find collections that share an attribute.

```bash
refget seqcol search [--names DIGEST] [--lengths DIGEST] [--sequences DIGEST] [--server URL]
```

The attribute digest is the digest of an attribute array (e.g., from level 1 output).

**Options:**

- `--names`: Names array digest to search for
- `--lengths`: Lengths array digest to search for
- `--sequences`: Sequences array digest to search for
- `--server, -s`: Server URL override

**Example workflow:**
```bash
# Get names digest from level 1
names_digest=$(refget fasta seqcol genome.fa --level 1 | jq -r '.names')

# Search for collections with same names
refget seqcol search --names $names_digest
```

### seqcol attribute

Retrieve the actual array values for an attribute digest.

```bash
refget seqcol attribute ATTRIBUTE_NAME DIGEST [--server URL]
```

**Examples:**
```bash
refget seqcol attribute lengths cGRMZIb3AVgkcAfNv39RN7hnT5Chk7RX
refget seqcol attribute names Fw1r9eRxfOZD98KKrhlYQNEdSRHoVxAG
```

### seqcol info

Get server information and capabilities.

```bash
refget seqcol info [--server URL]
```

Returns service info including supported algorithms and features.

---

## Admin Commands

Database administration and bulk loading operations.

### admin status

Show admin/database connection status.

```bash
refget admin status
```

Tests the database connection and displays connection info and table statistics.

### admin info

Show system info (version, dependencies, etc.).

```bash
refget admin info [--json]
```

### admin load

Load seqcol metadata from FASTA or JSON into PostgreSQL.

```bash
refget admin load [INPUT_FILE] [--pep PEP] [--pephub PROJECT] [--fa-root PATH] [--name NAME]
```

Can load from:

- Single FASTA file
- Single `.seqcol.json` file
- Batch from PEP project file (`--pep`)
- Batch from PEPhub project (`--pephub`)

**Options:**

- `--pep`: PEP project file for batch loading
- `--pephub`: PEPhub project (e.g., `nsheff/human_fasta_ref`)
- `--fa-root`: Root directory for FASTA files (used with `--pep`/`--pephub`)
- `--name, -n`: Human-readable name for the FASTA

**Examples:**
```bash
refget admin load genome.fa
refget admin load genome.fa --name "Human GRCh38"
refget admin load genome.seqcol.json
refget admin load --pep genomes.yaml --fa-root /data/fasta
refget admin load --pephub nsheff/human_fasta_ref --fa-root /data/fasta
```

### admin register

Upload a FASTA file to S3 and create a DRS record.

```bash
refget admin register FASTA --bucket BUCKET [--prefix PREFIX] [--cloud CLOUD] [--region REGION] [--digest DIGEST]
```

Does NOT load seqcol metadata. Use `ingest` for combined operation, or run `load` first.

**Required Options:**

- `--bucket, -b`: S3 bucket name for upload

**Optional Options:**

- `--prefix, -p`: S3 key prefix (default: none)
- `--cloud, -c`: Cloud provider (default: aws)
- `--region, -r`: Cloud region (default: us-east-1)
- `--digest, -d`: Seqcol digest (if not provided, will be computed from FASTA)

**Examples:**
```bash
refget admin register genome.fa --bucket my-refget-bucket
refget admin register genome.fa -b my-bucket -p fasta/ -c aws -r us-west-2
refget admin register genome.fa -b my-bucket --digest abc123...
```

### admin ingest

Load seqcol metadata AND register FASTA with cloud storage (combined operation).

```bash
refget admin ingest [FASTA] --bucket BUCKET [--prefix PREFIX] [--cloud CLOUD] [--region REGION] [--pep PEP] [--pephub PROJECT] [--fa-root PATH] [--name NAME]
```

Combines `load` and `register` in a single operation:

1. Parse FASTA and extract seqcol metadata
2. Store metadata in PostgreSQL
3. Upload FASTA to S3
4. Create DRS record for access

**Required Options:**

- `--bucket, -b`: S3 bucket name for upload

**Optional Options:**

- `--prefix, -p`: S3 key prefix
- `--cloud, -c`: Cloud provider (default: aws)
- `--region, -r`: Cloud region (default: us-east-1)
- `--pep`: PEP project file for batch ingestion
- `--pephub`: PEPhub project (e.g., `nsheff/human_fasta_ref`)
- `--fa-root`: Root directory for FASTA files (used with `--pep`/`--pephub`)
- `--name, -n`: Human-readable name for the FASTA

**Examples:**
```bash
refget admin ingest genome.fa --bucket my-bucket
refget admin ingest genome.fa -b my-bucket --name "Human GRCh38"
refget admin ingest --pep genomes.yaml --fa-root /data/fasta --bucket my-bucket
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `REFGET_CONFIG` | Path to configuration file |
| `REFGET_STORE` | Path to local RefgetStore |
| `REFGET_STORE_PATH` | Alternative for store path |
| `REFGET_DATABASE_URL` | PostgreSQL connection URL |
| `POSTGRES_HOST` | Database host |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General failure |
| 2 | File not found |
| 3 | Network error |
| 4 | Configuration error |

---

## Configuration File

The configuration file is located at `~/.refget/config.toml`:

```toml
[store]
path = "~/.refget/store"

[seqcol_servers]
default = "https://seqcolapi.databio.org"

[admin]
postgres_host = "localhost"
postgres_db = "refget"
postgres_user = "postgres"
```
