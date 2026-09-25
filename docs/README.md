
<div class="page-hero">
<img src="img/refget_logo.svg" alt="Refget" class="page-hero-logo" width="300" />
<p class="page-hero-tagline">Python package</p>
<div class="badges">
<a href="https://pypi.org/project/refget/"><img src="https://img.shields.io/pypi/v/refget"></a>
<a href="https://github.com/refgenie/refget"><img src="https://img.shields.io/badge/source-github-354a75?logo=github"></a>
<iframe src="https://ghbtns.com/github-btn.html?user=refgenie&repo=refget&type=star&count=true" frameborder="0" scrolling="0" width="80" height="20" title="GitHub"></iframe>
</div>
</div>

## The refget Python package

The `refget` Python package provides a Python implementation of the [GA4GH Refget Specifications](https://ga4gh.github.io/refget/), which define standards for identifying and distributing reference biological sequences, like reference genomes. It provides standards at 3 levels of data: sequences, sequence collections, and pangenomes (in progress).

<p align="center">
<img src="img/refget-umbrella.svg" width="500">
</p>


### The `refget` Python package includes these capabilities:


| Standard | Local use<br>(computing digests locally)   | Client<br>(connecting to a remote API) | API<br>(implementing an http interface) | Agent<br>(managing a SQL database) |
|:--------:|:---------:|:------:|:----:|:----:|
| Sequences | ✓ | ✓ | ✓ | ✓ |
| Sequence Collections | ✓ | ✓ | ✓ | ✓ |
| Pangenomes | ✗ | ✗ | ✓ | ✓ |

## Package components

The `refget` package provides several components for working with GA4GH refget standards:

- **Local digest functions** - Python interface to fast Rust-based implementations of GA4GH digests for sequences and sequence collections.

- **RefgetStore** - High-performance local storage for sequences and collections. Supports in-memory and on-disk modes, sequence retrieval by digest, FASTA export, and connecting to remote stores.

- **Clients** - For interacting with remote Refget APIs: `SequenceClient`, `SequenceCollectionClient`, and `FastaDrsClient`.

- **Agents** - For creating refget services with a PostgreSQL database backend. `RefgetDBAgent` is the primary interface.

- **FastAPI router** - Implements the refget API endpoints. Attach to an existing FastAPI service to deploy your own sequence collections API.

- **Compliance tests** - Evaluate a remote API instance against the sequence collections standard.

- **CLI** - Commands for computing digests (`refget fasta`), managing local stores (`refget store`), querying remote servers (`refget seqcol`), and database administration (`refget admin`).

## How the pieces fit together

Installing `refget` pulls in three layers that are developed in two repositories.

| Layer | What it is | Where it lives |
|-------|------------|----------------|
| **gtars-refget** | The Rust core: digest algorithms, alphabet detection and encoding, the RefgetStore on-disk format, the FASTA import pipeline, and the store types | The [gtars](https://github.com/databio/gtars) Rust workspace |
| **gtars (Python bindings)** | A PyO3 extension module exposing the Rust types to Python as `gtars.refget` | The `gtars-python` crate in the same workspace, published to PyPI as `gtars` |
| **refget** | The Python package: clients, the FastAPI router, the database agent, compliance tests, the CLI, and thin re-exports of the bindings | The [refget](https://github.com/refgenie/refget) repository |

The layers divide along a clear line. Anything that touches sequence bytes at scale, meaning digesting, encoding, storing, and retrieving, is implemented once in Rust and reached through the bindings. Anything that talks HTTP, SQL, or JSON schemas is implemented in Python.

The PyO3 bindings are a translation layer, not a reimplementation. Each Python class wraps the corresponding Rust struct and forwards calls to it, converting arguments and results at the boundary. There is no second copy of the digest logic, so a digest computed by the Python API, the CLI, the R bindings, or the Rust library is the same digest computed by the same code.

Because `gtars` is a compiled dependency, `refget` guards against its absence: `refget.const.GTARS_INSTALLED` reports whether the extension module loaded, and the store re-exports are `None` when it did not. Import the store types from `refget.store`:

```python
from refget.store import RefgetStore, digest_fasta
```

This is equivalent to importing from `gtars.refget` directly, but it keeps your code pointed at the package's stable surface.

## Install

```console
pip install refget
```

## Quick start

### Compute a sequence collection digest from a FASTA file

```bash
refget fasta digest genome.fa
```

### Query a remote seqcol server

```bash
# Get a collection by digest
refget seqcol show XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk

# Compare two collections
refget seqcol compare digest1 digest2

# List collections on the server
refget seqcol list
```

### Use the Python client

```python
from refget.clients import SequenceCollectionClient

client = SequenceCollectionClient()
collection = client.get_collection("XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk")
print(collection)
```

### Set up a local RefgetStore

RefgetStore is basically an attempt to:

- solve efficiency issues with the original refget sequences protocol.
- provide a way to download the actual data in a sequence collection, which is not provided by the current sequence collection standard.

```bash
# Initialize a local store
refget store init

# Import a FASTA file
refget store add genome.fa

# Export sequences
refget store export <digest> --output output.fa
```

For a hands-on walkthrough, see the [Getting Started tutorial](using-services/getting-started.py).
