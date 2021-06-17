# Refget

## Introduction

The refget package provides a Python interface to both remote and local use of the refget protocol. This package serves 4 functions:

1. A lightweight python interface to a remote refget API.

2. Local caching of retrieved results, improving performance for applications that require repeated lookups.

3. A fully functioning local implementation of the refget protocol for local analysis backed by either memory, SQLite, or MongoDB.

4. Convenience functions for computing refget checksums from python and handling FASTA files directly.

## Install

```console
pip install refget
```

## Basic use

### Retrieve results from a RESTful API

```python
import refget

rgc = RefGetClient("https://refget.herokuapp.com/sequence/")
rgc.refget("6681ac2f62509cfc220d78751b8dc524", start=0, end=10)

```

### Compute digests locally

```python
refget.trunc512_digest("TCGA")
```

### Insert and retrieve sequences with a local database

```python
checksum = rgc.load_seq("GGAA")
rgc.refget(checksum)
```

For more details, see the [tutorial](tutorial.md).
