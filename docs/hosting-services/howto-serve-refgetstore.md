# How to serve a RefgetStore concurrently

Serve GA4GH sequence collection endpoints from a local RefgetStore, with the store shared across request threads instead of locked per request. No database is required.

!!! info "Prerequisites"
    - A RefgetStore on local disk (`refget store init` and `refget store add`, or [the RefgetStore tutorial](../using-services/refgetstore.py))
    - `pip install refget fastapi uvicorn`
    - Familiarity with the [readonly store and its preloading requirements](../readonly-store-explained.md)

## 1. Open the store and preload

Open the store with the mutable `RefgetStore` type, then load everything the service will need. `ReadonlyRefgetStore` cannot lazy-load, so anything not loaded here will be unavailable at request time.

```python
from refget.store import RefgetStore

store = RefgetStore.open_local("/data/refget-store")
store.set_quiet(True)
store.load_all_collections()
```

`load_all_collections()` is the requirement for level 2 retrieval, comparison, and attribute lookup. Level 1 digests and collection listing work without it, but load it anyway unless startup time is critical: it reads metadata only, not sequence bytes.

To confirm what you have:

```python
info = store.stats()
print(info["n_collections"], "collections;", info["n_collections_in_memory"], "in memory")
```

## 2. Convert to a readonly store

```python
readonly = store.into_readonly()
```

After this call, `store` is empty and must not be used. Use `readonly` from here on.

## 3. Wire the store into a FastAPI app

`setup_backend` wraps whatever store you hand it in a `RefgetStoreBackend` and attaches it to `app.state.backend`. It does not load or convert anything, so the store you pass must already be in its final state.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from refget.router import create_refget_router, setup_backend
from refget.store import RefgetStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = RefgetStore.open_local("/data/refget-store")
    store.set_quiet(True)
    store.load_all_collections()
    setup_backend(app, store=store.into_readonly())
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(
    create_refget_router(collections=True, sequences=False),
    prefix="/seqcol",
)
```

Doing the load inside `lifespan` keeps startup cost in one place and guarantees the backend is ready before the first request is accepted.

## 4. Run with a thread pool

FastAPI dispatches synchronous route handlers to a thread pool, so a single process serves many requests in parallel against the one shared store. Run one worker process per machine and let the threads do the concurrency; each additional process would hold its own full copy of the store in memory.

```bash
uvicorn myapp:app --host 0.0.0.0 --port 8100 --workers 1
```

## 5. Verify

```bash
curl -s http://localhost:8100/seqcol/list/collection | head
curl -s http://localhost:8100/seqcol/collection/<digest>?level=2
```

Success looks like: collection listing returns a `results` array and a `pagination` object, level 2 retrieval returns `names`, `lengths`, and `sequences` arrays, and response times stay flat as you increase concurrent clients. If a collection request returns an error mentioning that the collection is not loaded, step 1 was skipped or incomplete.

## Serving sequence endpoints

Sequence and substring endpoints need more preloading, and the requirement differs by store location.

For a **local** store, sequence bytes are read directly from `.seq` files even for records that were never promoted, so `load_all_collections()` is sufficient for `get_substring` and `get_substrings`. Add `load_all_sequences()` only if you want every sequence resident in RAM.

For a **remote-backed** store, the sequence index is deferred until first access and the readonly store cannot fetch it. Call `load_all_sequences()` before converting, which downloads every sequence into the local cache. In practice, mirror the store locally rather than serving sequence bytes straight from a remote source.

!!! note
    `RefgetStoreBackend.substrings_from_regions()` delegates to the store's `substrings_from_regions()`, which the Python `ReadonlyRefgetStore` does not expose. Region extraction through the backend therefore requires a mutable `RefgetStore`, which is single-reader-oriented. Serve region extraction from a separate process, or use `get_substrings()` on the readonly store directly.

## Choosing this over a database backend

`RefgetStoreBackend` covers the core seqcol operations: retrieval at both levels, comparison, attribute search, and listing. Pangenome endpoints, DRS endpoints, and the database-only administrative routes require `RefgetDBAgent` and PostgreSQL. See [adding a FastAPI router](fastapi_router.md) for the database-backed setup.

!!! success "Key points"
    - `ReadonlyRefgetStore` does not lazy-load; every collection served must be loaded before `into_readonly()`
    - In Python, `into_readonly()` empties the source store, so switch to the returned object
    - `setup_backend(app, store=...)` wraps the store as-is and performs no loading of its own
    - One process with a thread pool is the intended deployment shape; extra worker processes duplicate the store in memory
