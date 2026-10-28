# How FASTA import works

Importing a FASTA file into a RefgetStore is not a single pass. Each record has to be read and decompressed, hashed twice (SHA-512/24u for the refget digest and MD5 for interoperability), inspected to choose an alphabet, bit-packed into that alphabet, and written to a `.seq` file. Done naively, that is a sequence of blocking steps where the CPU idles during I/O and the disk idles during hashing, with whole chromosomes accumulating in memory along the way.

RefgetStore instead runs these steps as a pipeline. This page explains the shape of that pipeline and why importing a large genome stays fast without its memory use growing with the size of the collection.

## Three stages, joined by bounded channels

Each FASTA file is processed by a chain of three stages running on dedicated threads:

1. **Read and decompress.** A reader opens the file and yields one record at a time. Compression is detected from the file rather than assumed, so plain and gzipped FASTA are handled by the same code path with no flag to set. (FAI offset tracking is skipped for gzipped input, since compressed files cannot be seeked into.)
2. **Digest.** The raw bytes of each record are hashed to produce the SHA-512/24u refget digest and the MD5 digest, and scanned to determine which alphabet the sequence uses.
3. **Encode.** The record is bit-packed using the alphabet chosen in stage 2: 2 bits per base for plain ACGT, 3 or 4 bits when ambiguity codes appear, 5 bits for protein, 8 bits as an ASCII fallback. See the [encoding comparison](reference/encoding-comparison.md) for the details of each scheme.

The stages are joined by **bounded** channels rather than queues that grow on demand. The channels between stages hold a single record, so at most a couple of contigs are in flight at once. When a downstream stage falls behind, the upstream stage blocks on send instead of buffering ahead. That backpressure is what turns a three-stage pipeline into a memory-bounded one: throughput is set by the slowest stage, and peak memory is set by the channel depth, not by the file size.

## Very large sequences bypass the pipeline

Passing a record between stages means it is briefly reachable from more than one place. For a 16 kb mitochondrial genome this is irrelevant. For a 250 Mbp chromosome, and more so for the multi-hundred-megabase contigs that appear in some assemblies, holding extra copies in flight is exactly what a bounded pipeline was supposed to avoid.

Records whose raw bytes exceed a threshold of **500 MB** are therefore digested and encoded inline on the reader thread and handed downstream already finished. The stages pass them along untouched. This costs a small amount of parallelism on the handful of records where it applies, in exchange for keeping the memory ceiling intact where it matters most. The import reports these records as it processes them.

## Across files: parallelism and a single writer

Concurrency across files is controlled by one knob: `jobs`, the number of input FASTA files built concurrently. Each file gets its own decoder, so with several files gzip decompression proceeds in parallel; `0` means auto (based on available parallelism) and `1` means serial. With a single input file the setting has no effect, since the per-file pipeline is already the parallelism.

```python
from refget.store import RefgetStore

store = RefgetStore.on_disk("/data/refget-store")
results = store.add_sequence_collections_from_fastas("fasta/*.fa.gz", jobs=4)
for metadata, was_new in results:
    print(metadata.digest, "added" if was_new else "already present")
```

Note that `add_sequence_collections_from_fastas` returns a list of `(metadata, was_new)` tuples, and the single-file `add_sequence_collection_from_fasta` returns one such tuple.

The building half (decompress, parse, digest, encode) touches no shared store state and runs concurrently. Registration is different: sequences, collections, name lookups, and aliases are inserted by a **single** owner thread. Builders stream finished sequences to that inserter one at a time over another bounded channel, and the inserter writes each `.seq` file and then drops the bytes, retaining only lightweight metadata. Peak memory during a multi-file import is therefore bounded by roughly `jobs` times the channel depth times the average encoded sequence size, independent of how many sequences a collection contains. The `.seq` byte writes themselves are dispatched to a bounded pool of writer threads, since writes to distinct digests cannot conflict.

The result is deterministic. Index files are written once at the end, sorted by content and collection digest, so a store built with `jobs=8` is byte-identical to the same store built serially, regardless of which builder finished first.

## The RGSI cache: importing the same FASTA twice

Digesting is the expensive part of import and it is entirely a function of the file's contents. Repeating it on a re-import is pure waste.

When importing into a disk-backed store, RefgetStore writes an `.rgsi` sidecar next to the source FASTA, named by stripping the `.fa`, `.fasta`, `.fa.gz`, or `.fasta.gz` suffix and appending `.rgsi`. The sidecar holds the collection metadata and the per-sequence metadata: names, lengths, alphabets, and both digests.

On a later import of the same file, the sidecar is read first, which enables two shortcuts:

- **The collection is already in the store.** Its digest is known from the sidecar without opening the FASTA, so the file is never read, decompressed, or encoded. The import reports the collection as skipped.
- **The collection is not in the store** (a fresh store, or a store being rebuilt). Stage 2 is skipped entirely: the file is decompressed and encoded, with metadata taken from the cache rather than recomputed.

If the sidecar is missing, unreadable, empty, or inconsistent with the FASTA (for example, it lists a sequence name the file does not contain), it is discarded and the full pipeline runs. A stale cache costs time, not correctness.

You can generate the sidecar ahead of time without importing anything:

```bash
refget fasta rgsi genome.fa.gz
```

## Failure behavior

Import is not transactional. If a build or write fails partway through, sequences already emitted for the failing collection may have been written to disk and registered in memory, while the collection itself was never finalized. Those sequences are orphans: referenced by no collection.

On error, the import performs a best-effort cleanup, removing any sequence not referenced by a surviving collection, along with its `.seq` file. The in-memory store is left internally consistent, with no dangling references. If you need a guaranteed-clean store after a failed import, rebuild it rather than resuming.

## Related reading

- [RefgetStore encoding](reference/encoding-comparison.md) for the alphabets and bit-packing schemes chosen in stage 3
- [RefgetStore file format](reference/refgetstore-format.md) for the `.rgsi` sidecar layout and the on-disk structure import produces
- [CLI reference](reference/cli.md) for `refget store add` and `refget fasta rgsi`
