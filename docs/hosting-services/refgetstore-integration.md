# How RefgetStore integrates with refgenie

RefgetStore is a content-addressed sequence database (from [gtars](https://github.com/databio/gtars)) that stores sequences and sequence collections by digest. Refgenie uses RefgetStore differently depending on whether it's running as a local client or as a server, controlled by a mode system.

## Two modes, two relationships to RefgetStore

```
                   Remote RefgetStore (S3/HTTP)
                   ┌─────────────────────────────┐
                   │ sequences + collections      │
                   │ aliases/ncbi.tsv             │
                   │ aliases/insdc.tsv            │
                   │ collections/*.fhr.json       │
                   └──────────┬──────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼                               ▼
   refgenie client (local)         refgenieserver
   ┌──────────────────┐          ┌──────────────────┐
   │ SQLite            │          │ PostgreSQL        │
   │  - genomes        │          │  - aliases (flat) │
   │  - assets         │          │  - genomes        │
   ├──────────────────┤          ├──────────────────┤
   │ Local RefgetStore │          │ Remote store cache │
   │  (owned, on_disk) │          │  (not owned,       │
   │  - sequences      │          │   open_remote)     │
   │  - aliases/       │          │  - aliases (pulled) │
   │    refgenie.tsv   │          │  - fhr (pulled)    │
   └──────────────────┘          └──────────────────┘
```

| | Local client | Server |
|---|---|---|
| **Database** | SQLite | PostgreSQL |
| **RefgetStore mode** | `on_disk()` — owned, read/write | `open_remote()` — not owned, read-only with local cache |
| **Alias source of truth** | RefgetStore "refgenie" namespace (`StoreAliasManager`) | SQL alias table (`AliasManager`) |
| **Writes to store** | Yes | No |
| **Mode class** | `LocalMode` | `ServerMode` |

Mode is determined at `Refgenie.__init__()` based on whether a `refget_store_url` is provided.

## Client-side: local RefgetStore

The local CLI maintains a RefgetStore at `genome_folder/.refget_store/`. Refgenie creates and owns this store via `LocalMode`.

### Adding a genome

```bash
refgenie genome init --fasta hg38.fa.gz --name hg38 --description "Human GRCh38"
```

This:

1. Loads sequences into the local RefgetStore via `store.add_sequence_collection_from_fasta()` and computes the collection digest
2. Registers the genome in SQLite with the digest
3. Writes the alias "hg38" to the RefgetStore's "refgenie" namespace via `StoreAliasManager`

The store is the single source of truth for aliases in local mode. Any tool that opens the RefgetStore directly (without refgenie) can resolve genome names.

### Retrieving sequences

```bash
refgenie getseq hg38 chr1:0-1000
```

Resolution:

1. `StoreAliasManager.resolve("hg38")` → digest (from RefgetStore "refgenie" namespace)
2. `store.get_sequence_by_name(digest, "chr1")` → sequence record
3. `store.get_substring(seq_digest, 0, 1000)` → `"ATCG..."`

No FASTA file is needed after initialization. Sequences are content-addressable and deduplicated.

### Remote genomes

You can also point refgenie at a remote source:

```bash
refgenie genome init \
  --remote-url http://seqcolapi.databio.org \
  --remote-digest abc123... \
  --name hg38 --description "Human GRCh38"
```

Refgenie auto-detects whether the URL points to a seqcolapi server or a static RefgetStore (by checking for `rgstore.json` via `make_source()`). Sequences are fetched on-demand when you call `getseq` and cached in the local RefgetStore.

## Server-side: remote RefgetStore with PostgreSQL

The server does **not** own a local RefgetStore. Instead, it connects to a remote RefgetStore (on S3 or HTTP) via `open_remote()`, caching data locally in an ephemeral directory. PostgreSQL is the persistent store for aliases, genomes, and assets.

### Server startup

The server is configured via the `REFGENIE_REFGET_STORE_URL` environment variable:

```python
from refgenie.config import REFGENIE_REFGET_STORE_URL
refgenie = Refgenie(refget_store_url=REFGENIE_REFGET_STORE_URL)
```

When `refget_store_url` is set, `Refgenie` creates a `ServerMode`, and at startup:

1. `ServerMode.create_store()` opens the remote RefgetStore with a local cache directory
2. `store.pull_aliases()` — syncs all reference alias namespaces from remote to cache
3. `store.pull_fhr()` — syncs all FHR provenance metadata from remote to cache

After startup, all alias resolution and metadata lookups are in-process — no per-request remote calls.

### Populating the remote RefgetStore

The server reads from the store but never writes to it. Populating the store is a separate admin process:

1. **Build the RefgetStore** from FASTA files (using gtars or `refget store add`)
2. **Host it** on S3, HTTP, or any static file server
3. **Point the server at it** via the `REFGENIE_REFGET_STORE_URL` environment variable

### Loading metadata into PostgreSQL

The server also creates a `RefgetDBAgent` backed by PostgreSQL for serving the seqcol REST API:

```python
from refget.agents import RefgetDBAgent
app.state.dbagent = RefgetDBAgent(engine=refgenie.database_engine)
```

Server-specific metadata (seqcol collections, DRS records) is loaded via `refget admin`:

```bash
# Load a single genome
refget admin load genome.fa --name "Human GRCh38"

# Batch load from a PEP
refget admin load --pep genomes.yaml --fa-root /data/fasta/

# Load + upload FASTA to S3 + create DRS record
refget admin ingest genome.fa --bucket my-refget-bucket --name "Human GRCh38"

# Batch ingest from PEP
refget admin ingest --pep genomes.yaml --fa-root /data/fasta/ --bucket my-refget-bucket
```

The `load` command parses each FASTA, computes the seqcol metadata (names, lengths, sequence digests), and stores it in PostgreSQL. The `ingest` command additionally uploads the FASTA to S3 and creates a DRS access method record.

### How alias resolution works on the server

When a client queries an alias (e.g. `GET /v4/aliases/hg38`):

1. Check the SQL alias table (PostgreSQL) — server policy aliases always win
2. If not found, check RefgetStore collection aliases across all namespaces (ncbi, insdc, ucsc, etc.)
3. If found, return the full genome record: digest + seqcol level 2 + FHR metadata

```json
{
  "alias": "hg38",
  "digest": "f1b5a389...",
  "source": "server",
  "collection": {
    "names": ["chr1", "chr2", "..."],
    "lengths": [248956422, 242193529, "..."],
    "sequences": ["SQ.abc...", "SQ.def...", "..."]
  },
  "fhr": {
    "species": "Homo sapiens",
    "assembly_accession": "GCF_000001405.40"
  }
}
```

### Service info

The server exposes its RefgetStore URL and capabilities in `/seqcol/service-info`, so clients can discover the backing store and access sequences directly:

```json
{
  "id": "org.refgenie.seqcol",
  "seqcol": {
    "refget_store": {
      "enabled": true,
      "url": "https://my-bucket.s3.amazonaws.com/refget_store/"
    }
  }
}
```

### Without a RefgetStore

When `REFGENIE_REFGET_STORE_URL` is not set, the server operates in local mode:

- Alias resolution uses the RefgetStore "refgenie" namespace (same as client)
- No reference namespace lookups (ncbi, insdc, etc.)
- Asset management works normally

### Database configuration

```bash
export POSTGRES_HOST=localhost
export POSTGRES_DB=refget
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=yourpassword
```

## Typical deployment workflow

1. **Build a RefgetStore** from your FASTA files (using `refget store add` or gtars directly)
2. **Host it** on S3 or any static file server
3. **Set up PostgreSQL**
4. **Load metadata**: `refget admin ingest --pep genomes.yaml --fa-root /data/fasta/ --bucket my-bucket`
5. **Configure the server**: set `REFGENIE_REFGET_STORE_URL` to point at the hosted store
6. **Start the server**: `refgenie serve`
7. **Verify**: visit `/seqcol/service-info` and `/v4/aliases` on the running server

## How the two sides connect

A refgenie client can connect to a server as a remote source:

```bash
refgenie genome init \
  --remote-url http://myserver.com/seqcol \
  --remote-digest <digest> \
  --name hg38 --description "Human GRCh38"

# Sequences are fetched on demand and cached locally
refgenie getseq hg38 chr1:0-1000
```

The client uses `make_source()` to auto-detect whether the URL is a seqcolapi server or a static RefgetStore. If the server advertises a `refget_store_url` in its service-info, the client can use the store directly for sequence retrieval.

## See also

- [What is RefgetStore?](../refgetstore-explained.md) — overview of the storage format
- [Adding a FastAPI router](fastapi_router.md) — embedding seqcol endpoints in your own app
- [RefgetDB Agent](agent.ipynb) — programmatic database operations
- [CLI reference](../reference/cli.md) — full `refget admin` command reference
