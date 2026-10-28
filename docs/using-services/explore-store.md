# Explore a store in your browser

The [RefgetStore Explorer](https://refget.databio.org/explore-store) is a web app for browsing a store's
sequences, collections, aliases, and [FHR metadata](../reference/refgetstore-format.md).
It runs entirely in the browser, reading a store's static files directly over HTTP.

The `refget store explore` command points that Explorer at a store on your own machine:
it serves both the store's files and the Explorer web UI from a single local web server,
then opens your browser to it. This tutorial builds a small store from scratch and opens
it in the Explorer. It takes a couple of minutes and needs no internet connection.

## Before you start

Install refget with the store extra, which provides the `refget store` commands:

```console
pip install 'refget[store]'
```

## 1. Create a FASTA file

The Explorer browses a store, and a store is built from sequences. Create a tiny FASTA
file to work with:

```console
cat > demo.fa <<'FASTA'
>chr1 demo sequence one
ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT
GGGGCCCCAAAATTTTACGTACGTACGTACGTACGTACGT
>chr2 demo sequence two
TTTTAAAACCCCGGGGTTTTAAAACCCCGGGGTTTTAAAA
FASTA
```

Already have a genome FASTA on hand? Use that instead — any `.fa` or `.fa.gz` file works.

## 2. Build a store

Initialize an empty store, then import the FASTA into it:

```console
refget store init -p demo_store
refget store add demo.fa -p demo_store
```

`refget store add` digests each sequence and records a
[sequence collection](../genome-collections-explained.md) for the file. Check what landed
in the store:

```console
refget store stats -p demo_store
```

```json
{
  "storage_mode": "Encoded",
  "n_collections": "1",
  "n_sequences": "2"
}
```

## 3. Open the Explorer

Point the Explorer at your new store:

```console
refget store explore demo_store
```

This starts a local server on `http://127.0.0.1:8080` and opens your browser to the
Explorer, already loaded with `demo_store`. You'll land on the store overview, where you
can browse the collection from step 2, drill into its sequences, and inspect names,
lengths, and digests. Press `Ctrl-C` in the terminal to stop the server when you're done.

That's the whole loop: a FASTA on disk, a store, and a browsable view of it — no server
to deploy and no data leaving your machine.

## When to use it

Because the Explorer only needs static files, it works against a store anywhere — an S3
bucket, an HTTP server, or a directory on disk. The hosted Explorer at
[refget.databio.org](https://refget.databio.org/explore-store) already covers stores
reachable from the public internet. `refget store explore` covers the cases it can't:

- **A store on local disk.** Browsers can't `fetch()` `file://` URLs, so a store in a
  local directory needs a local web server to browse it.
- **A read-only mount**, such as a [CVMFS](https://cernvm.cern.ch/fs/) distribution of a
  reference store on a shared cluster.
- **An air-gapped or offline machine**, where the hosted Explorer is unreachable. The
  command bundles the Explorer web UI, so it works with no internet access.

## Options

| Option | Description |
|--------|-------------|
| `PATH` | Store directory to explore (falls back to your configured store path). |
| `--host` | Interface to bind (default `127.0.0.1`). |
| `--port`, `-P` | Port to serve on (default `8080`; auto-increments if busy). |
| `--no-browser` | Print the URLs instead of opening a browser. |
| `--store-only` | Serve only the store files, skipping the bundled UI — useful when hosting your own front end. |
| `--frontend-dir` | Serve a custom Explorer build from this directory. |

The command exposes read-only `GET`/`HEAD` access to the store's files. To modify a
store, use [`refget store add`, `pull`, and `alias`](../reference/cli.md).

## Serving on a shared server

To let others on your network reach a store hosted on a cluster login node, bind a
public interface and skip opening a local browser:

```console
refget store explore /cvmfs/data.example.org/refget-store --host 0.0.0.0 --no-browser
```

Then share the printed Explorer URL. See
[What is RefgetStore?](../refgetstore-explained.md) for background on the store format
and its local/remote symmetry.
