# RefgetStore sequence retrieval flows

A RefgetStore can be read from three places: sequence bytes may be **resident in memory**, sitting in a **local `.seq` file** on disk, or available only from a **remote HTTP store**. Because moving whole chromosomes is expensive, the store offers three distinct retrieval *flows* so you can match the cost to your access pattern instead of always paying for a full download.

This page is a reference for those flows: what each one fetches, what it costs, and when to use it.

## The three flows

| Flow | What it moves | Peak memory | Persists locally? | Repeated remote reads | Best for |
|------|---------------|-------------|-------------------|-----------------------|----------|
| **1. Partial read** (`get_substring`, `get_substrings`) | Only the bytes covering `[start, end)`, returned as a string | O(region) | No | Re-fetches each call | Sparse, random-access extraction — resident, local-disk, **or remote** (byte-range) |
| **2. Streaming** (`stream_sequence`) | Only the bytes covering `[start, end)`, as a byte/character stream — **local seek or remote HTTP `Range`** | O(1) in region length | No | Re-fetches each call | One-off or large region pulls, local or remote, without downloading whole sequences into memory |
| **3. Load &amp; cache** (`load_sequence`, `load_all_sequences`) | The **whole** sequence `.seq`, downloaded once | O(sequence) | Yes (under the local cache) | Served locally after first load | Repeated access to the same sequences; warm reuse across sessions |

Flows 1 and 2 both now reach a remote sequence with no preload: **1** returns the whole result at once, **2** streams it in bounded chunks. Neither downloads or caches the full sequence, and neither promotes the record to Full, so `n_sequences_in_memory` does not change either way.

The key trade-off is **flow 1/2 vs flow 3** for remote data:

- **Flows 1 and 2 (byte-range)** fetch only the bases you ask for. A 50 bp lookup transfers ~50 bytes. Nothing is cached, so a second read of the same region fetches again. Ideal for *sparse* extraction — a handful of loci scattered across a genome. Flow 1 returns the region as one string; flow 2 streams it in bounded chunks, useful when the region itself is large.
- **Flow 3 (load &amp; cache)** downloads the entire sequence (a whole chromosome can be tens of MB even encoded), persists it to the local cache, and holds it in memory. The first touch is expensive; every read afterward is local and fast. Ideal for *dense or repeated* access — e.g. converting an entire VCF against one assembly.

Once a sequence is resident (flow 3) or its `.seq` is on local disk, both `get_substring` and `stream_sequence` serve it from there with no network access at all.

## Source resolution

`get_substring`, `get_substrings`, and `stream_sequence` all resolve their byte source in the same order:

1. **Resident** — if the sequence is fully loaded (`Full`), read from the in-memory buffer.
2. **Local `.seq`** — if a local store path holds the file, do a positioned read of just the covering bytes (the whole sequence never enters RAM).
3. **Remote byte-range** — if the file is remote, issue an HTTP `Range:` request for the covering bytes and decode just that span. This requires the build's `http` feature.

None of the three steps promotes the record to Full or writes anything to the local cache; a byte-range read is a pure pass-through. To have a remote sequence served locally after the first touch, use **flow 3** (`load_sequence`, or `load_all_sequences`) instead.

## Choosing a flow

```
Need bases for a region of a sequence?
│
├─ One-off or sparse access (a handful of regions, read once)?
│     └─ Yes → Flow 1 (get_substring/get_substrings) or Flow 2 (stream_sequence)
│              -- both work resident, local, or remote; neither caches or loads the whole sequence
│
└─ Repeated access to the same sequence, or converting a whole file against it?
      └─ Flow 3: load_sequence (or load_all_sequences), then Flow 1/2 serve it from memory/disk
```

## Binding interface

The same three flows are exposed through a consistent interface across the bindings — Python, R, Node.js (native), and WebAssembly:

| Method | Flow | Notes |
|--------|------|-------|
| `get_substring(digest, start, end)` | 1 | Single region → string; resident/local/remote byte-range |
| `get_substrings(digest, ranges)` | 1 | Many regions of one sequence in a single call |
| `stream_sequence(digest, start, end)` | 2 | Region as a bounded-memory stream; local seek or remote byte-range |
| `load_sequence(digest)` | 3 | Download + cache + make resident |
| `load_all_sequences()` | 3 | Eagerly promote every sequence |

In the browser, WebAssembly has no synchronous disk or network access, so the fetch-and-cache machinery for flows 2 and 3 is driven from JavaScript (fetching `.seq` bytes, caching them in the Origin-Private File System) and handed to the in-memory wasm store. The method names mirror the native bindings so the mental model carries over.

!!! note
    The Rust core and the Python binding both resolve flow 1 (`get_substring`/`get_substrings`) and flow 2 (`stream_sequence`) against resident, local, and remote sequences via HTTP byte-range reads, as described above. Uniform coverage of all three flows across the R, Node.js, and WebAssembly bindings is still being rolled out; consult your binding's release notes for the exact methods currently available there.

## Related reference

- [RefgetStore file format](refgetstore-format.md) — the on-disk/remote directory layout, including the `sequences/<ab>/<digest>.seq` files these flows read.
- [RefgetStore encoding](encoding-comparison.md) — how `.seq` bytes map to bases, which determines the byte range a region read must fetch.
