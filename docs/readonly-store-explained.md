# The readonly store and concurrent access

RefgetStore exists in two types. `RefgetStore` is the one you use from a script or the CLI: it lazy-loads, so a read of something not yet resident quietly fetches it. `ReadonlyRefgetStore` is the one you use behind a server: its read methods borrow immutably, so a single instance can be shared across many threads at once.

The two types exist because those goals conflict. Lazy loading mutates the store, and a method that mutates cannot be called concurrently from several threads without a lock. Serving requests through a lock serializes them, which defeats the point of a fast local store. The readonly type resolves this by moving all the loading to a startup phase and leaving the request path with nothing left to mutate.

## What `into_readonly()` gives you

`RefgetStore` is a thin wrapper over a `ReadonlyRefgetStore`. Converting between them is a move, not a copy or a rebuild:

```rust
let mut store = RefgetStore::open_local("/path/to/store")?;
store.load_all_collections()?;
let readonly: ReadonlyRefgetStore = store.into_readonly();
let shared = std::sync::Arc::new(readonly);
```

The wrapper's lazy-loading read methods are gone; what remains is the inner store, whose query methods take `&self`. Because it holds no interior state requiring exclusive access on the read path, `Arc<ReadonlyRefgetStore>` can be cloned into every request handler and read from concurrently. Partial reads from `.seq` files go through a small internal file-descriptor cache guarded by a mutex, but the lock is held only long enough to look up or insert a handle; the actual positioned read happens outside it, so concurrent readers are not serialized.

The Python binding follows the same shape:

```python
from refget.store import RefgetStore

store = RefgetStore.open_local("/path/to/store")
store.load_all_collections()
readonly = store.into_readonly()
```

In Python, `into_readonly()` consumes the original: the source object is left holding an empty in-memory store and should not be used afterward. `ReadonlyRefgetStore` in Python has no constructor and no mutating methods at all; it is obtainable only through this call.

## What "readonly" does and does not mean

The name describes the read path, not the whole type. Two clarifications matter for deploying it correctly.

**In Rust, `ReadonlyRefgetStore` still has `&mut self` methods.** `load_sequence`, `load_all_collections`, `clear`, `enable_persistence`, `add_sequence_collection`, and `remove_collection` all exist on it. What the type guarantees is that its *queries* take `&self`. Once you place it in an `Arc` those mutating methods are unreachable, because `Arc` hands out shared references only. So the accurate framing is: reads are `&self`, and the value is safe to share across threads once you have finished mutating it and wrapped it.

**It does not lazy-load.** This is the constraint that catches people. A method that takes `&self` cannot promote a Stub record to Full, so anything not loaded before conversion stays unavailable. `get_collection` on a collection that was never loaded returns an error telling you to call `load_collection()` or `load_all_collections()` first; it does not go and fetch it.

That makes preloading the caller's responsibility, and what to preload depends on which endpoints you serve:

| Serving | Preload before `into_readonly()` |
|---------|----------------------------------|
| Collection listing and level 1 attribute digests | Nothing beyond opening the store; collection metadata comes from `collections.rgci` |
| Collection level 2, comparison, attribute lookup | `load_all_collections()` |
| Sequences and substrings from a **local** store | `load_all_collections()`; sequence bytes are read from `.seq` files on demand even for Stub records |
| Sequences and substrings from a **remote** store | `load_all_collections()` and `load_all_sequences()` |

The remote case deserves care. A remote store defers its sequence index (see [How RefgetStore defers loading](lazy-loading-explained.md)), so a readonly store converted from a freshly opened remote store has no sequences visible at all until the index is loaded. In Rust, `load_sequence_index()` loads just the index without downloading any sequence bytes. The Python binding does not currently expose that method, so the practical options in Python are `load_all_sequences()`, which downloads every sequence into the cache, or a single `load_sequence(digest)` call, which pulls the index plus that one sequence. Serving sequence bytes from a remote-backed readonly store in Python effectively means mirroring the data locally first.

## The `SeqColService` trait

On the Rust side, the read-only operations a GA4GH sequence collections API server needs from its backend are captured in a trait:

```rust
pub trait SeqColService {
    fn get_collection_level1(&self, digest: &str) -> Result<CollectionLevel1>;
    fn get_collection_level2(&self, digest: &str) -> Result<CollectionLevel2>;
    fn compare(&self, digest_a: &str, digest_b: &str) -> Result<SeqColComparison>;
    fn compare_with_level2(&self, digest_a: &str, external: &CollectionLevel2)
        -> Result<SeqColComparison>;
    fn find_collections_by_attribute(&self, attr_name: &str, attr_digest: &str)
        -> Result<Vec<String>>;
    fn get_attribute(&self, attr_name: &str, attr_digest: &str)
        -> Result<Option<serde_json::Value>>;
    fn list_collections(&self, page: usize, page_size: usize, filters: &[(&str, &str)])
        -> Result<PagedResult<SequenceCollectionMetadata>>;
    fn collection_count(&self) -> usize;
}
```

Every method takes `&self` and returns a concrete type, which makes the trait object-safe: a server can hold `Arc<dyn SeqColService>` and stay agnostic about what is behind it. A filesystem-backed store, a Postgres-backed service, a proxy to a remote API, or an in-memory mock in a test can all satisfy the same interface.

`ReadonlyRefgetStore` is the only implementation of `SeqColService` in the codebase. In particular the mutable `RefgetStore` does **not** implement it, and cannot: the trait requires `&self` methods, and `RefgetStore`'s equivalents take `&mut self` so they can lazy-load. This is a deliberate compile-time push toward the readonly type for anything server-shaped.

The trait is a Rust-level interface and is not exposed through the Python bindings. Python has an analogous but separate abstraction: the `SeqColBackend` protocol in the `refget` package, implemented by `RefgetStoreBackend` (store-backed) and `RefgetDBAgent` (Postgres-backed).

## Related reading

- [How to serve a RefgetStore concurrently](hosting-services/howto-serve-refgetstore.md) for the deployment recipe
- [How RefgetStore defers loading](lazy-loading-explained.md) for the Stub/Full model and remote index deferral
- [RefgetStore retrieval flows](reference/refgetstore-retrieval-flows.md) for what each read method actually moves
