# How RefgetStore defers loading

A RefgetStore can describe far more data than you want to move. A store holding a few thousand reference genomes has a sequence index of tens of megabytes and hundreds of gigabytes of sequence bytes behind it. Opening such a store and asking "which collections are here?" should not require downloading any of that.

RefgetStore handles this with deferral at two levels: individual **records** exist as metadata-only placeholders until something asks for their data, and for remote stores the **index files** themselves are fetched on demand. This page explains both mechanisms and what they imply for how a store behaves.

## Records: Stub and Full

Every sequence and every collection in a store is held as one of two variants.

| Variant | Sequence record | Collection record |
|---------|-----------------|-------------------|
| **Stub** | Metadata only: name, length, alphabet, `sha512t24u`, `md5`, description | Metadata only: collection digest and the attribute digests (names, lengths, sequences, and the ancillary digests) |
| **Full** | Metadata plus the sequence bytes | Metadata plus the list of member sequence records |

Loading a store parses index files, which contain only metadata, so every record starts as a Stub. Nothing has been read from a `.seq` file and no per-collection `.rgsi` file has been opened.

A record is promoted to Full on first access:

- A sequence is promoted when its bytes are fetched, either by an explicit `load_sequence(digest)` or lazily when a read method needs them. The bytes are read from the local `.seq` file, or downloaded from the remote store and written into the local cache.
- A collection is promoted when its `collections/<digest>.rgsi` file is read, which also populates the name lookup table that maps sequence names to digests within that collection.

Promotion is sticky. Once a record is Full it stays resident until you call `clear()`, which drops all sequence records and preserves the metadata, collections, name lookups, MD5 lookups, aliases, and FHR metadata.

You can inspect the state of the store directly:

```python
from refget.store import RefgetStore

store = RefgetStore.open_local("/path/to/store")

info = store.stats()
print(info["n_sequences"], info["n_sequences_in_memory"])
print(info["n_collections"], info["n_collections_in_memory"])

record = store.get_sequence("2i7v3vX9EDUnPWlkZMxaMFI2P0hDMOFC")
print(record.is_loaded)
```

Note that `is_loaded` reports whether the record holds bytes in memory, not whether the sequence exists in the store. A Stub in a disk-backed store is fully retrievable; it just has not been read yet.

## Indexes: what a remote store downloads when

For a local store, the index files are already on disk and reading them is cheap, so both are parsed at open time. For a remote store the same files must be fetched over the network, and the sequence index is by far the larger of the two: `sequences.rgsi` carries one line per sequence, which reaches tens of megabytes for a store holding thousands of assemblies.

`open_remote()` re-fetches `rgstore.json` on every call, so it always sees the current manifest even if a local cache from an earlier session already exists. It keeps a per-origin cache directory (keyed off the remote URL) under `<store>/.remote_cache/<hash>/`, marked with a `.origin` file so a cache can't accidentally be reused against a different remote. Opening a remote store fetches, up front:

- `rgstore.json`, the refreshed manifest
- `collections.rgci`, the collection index, which yields one Stub collection record per collection
- every sequence and collection alias namespace the manifest declares (`aliases/sequences/<ns>.tsv`, `aliases/collections/<ns>.tsv`); a namespace the manifest advertises but the remote can't actually serve is an error, not a silent skip

`sequences.rgsi` is left alone. It is downloaded the first time a sequence-level operation actually needs it -- either a whole-sequence read (`load_sequence`, `get_sequence_by_name`, ...), which also caches the sequence, or a substring read. Until then the store knows every collection that exists, can list and filter them, and can serve level 1 attribute digests, all without having transferred a sequence index or a single base.

Because the manifest is refreshed on every open, the cache is also where changes get reconciled: if the collection index, sequence index, alias, or FHR digest recorded in the new manifest differs from what the cache last saw, the corresponding cached index/artifact is invalidated and re-fetched. Cached `.seq` sequence payloads are left alone by this invalidation -- content-addressed by digest, they don't go stale.

```python
from refget.store import RefgetStore

# Fetches rgstore.json and collections.rgci only.
store = RefgetStore.open_remote("/tmp/refget-cache", "https://example.org/store/")

page = store.list_collections(page=0, page_size=10)
for meta in page["results"]:
    print(meta.digest, meta.n_sequences)
print(page["pagination"]["total"])

# This first sequence request triggers the sequences.rgsi download.
seq = store.get_sequence_by_name(page["results"][0].digest, "chr1")
```

Downloaded index files land in the local cache directory, so the deferral cost is paid once per cache rather than once per session.

## Store size without the sequence index

Deferring the sequence index creates a gap: a client that has not downloaded `sequences.rgsi` cannot sum sequence lengths, so it cannot answer "how big is this store?"

The manifest closes the gap. At index-write time the store computes the total logical size of all sequence payloads (each sequence's length converted through the storage mode's bits-per-symbol) and records it in `rgstore.json` as `logical_sequence_bytes`. A client reads it straight from the manifest it already downloaded:

```python
meta = store.store_metadata()
print(meta.get("logical_sequence_bytes"))
```

This value covers sequence payloads only. It excludes index files, alias files, FHR sidecars, and the manifest itself, and it is computed arithmetically rather than by walking the directory, so it reflects what the sequences *would* occupy rather than the exact current on-disk footprint.

## Where deferral stops

Lazy loading is a property of `RefgetStore`, the mutable wrapper type. Promoting a Stub to Full mutates the store, so every lazy-loading read method takes a mutable borrow.

`ReadonlyRefgetStore`, the variant intended for concurrent serving, does not lazy-load: its read methods borrow immutably and therefore cannot promote a record. Data must be preloaded before conversion. See [The readonly store and concurrent access](readonly-store-explained.md) for what to preload and why.

One exception is worth knowing. Substring retrieval (`get_substring`, `get_substrings`) never needs to promote a Stub to Full: it resolves its bytes as resident -> local `.seq` -> remote HTTP byte-range, reading only the span it needs at each step. Against a **local disk-backed** store this means a positioned read of just the covering bytes from the `.seq` file. Against a **remote-only** sequence it means an HTTP `Range:` request for just the covering bytes -- not a download of the whole chromosome, and not a promotion to Full, so `n_sequences_in_memory` does not change. The [retrieval flows reference](reference/refgetstore-retrieval-flows.md) covers the trade-offs between partial reads, streaming, and full loads.

## Related reading

- [RefgetStore file format](reference/refgetstore-format.md) for the manifest fields and index file layouts described here
- [RefgetStore retrieval flows](reference/refgetstore-retrieval-flows.md) for choosing between partial reads, streaming, and loading
- [The readonly store and concurrent access](readonly-store-explained.md) for preloading requirements when serving
