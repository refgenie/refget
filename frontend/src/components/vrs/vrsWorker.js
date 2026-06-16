// vrsWorker.js — heavy-lifting Web Worker for the HGVS/VCF → VRS page.
//
// Why a Worker:
//   1. OPFS *synchronous access handles* (createSyncAccessHandle) are Worker-only.
//      They give fast, seekable read()/write() over the Origin-Private File
//      System — our local genome cache.
//   2. Converting a large VCF must not block the UI thread; progress still
//      streams out via postMessage while the wasm compute loop runs.
//
// Mental model: WASM HAS NO I/O. This Worker fetches bytes (network or OPFS) and
// copies them into wasm linear memory. wasm32 has a hard 4 GB ceiling, so the
// reference is held ENCODED (2-bit packed) and decoded on the fly per variant.
//
// ONE GENOME, NO GUESSING. A refgetstore holds many *collections* (genomes /
// assemblies). The user picks exactly one. We then resolve chromosome names by
// EXACT match within that collection's own sequence index — no chr-prefix
// toggling, no cross-namespace alias probing. A name that isn't in the chosen
// genome is an error, not something to guess at. This removes all assembly
// ambiguity ("which chr20?"): you live in the genome you selected, period.
//
// LAZY loading: a genome has hundreds of contigs; an input touches a few. We
// fetch only the small collection index up front, then download a chromosome's
// encoded .seq only when an input references it — cached in OPFS for reuse.
//
// Store layout (gtars refgetstore):
//   rgstore.json                      — manifest (templates, namespaces)
//   collections.rgci                  — collection index (digest, n_sequences, …)
//   collections/<coll-digest>.rgsi    — that collection's sequences
//   aliases/collections/<ns>.tsv      — collection name -> collection digest
//   sequences/<ab>/<seq-digest>.seq   — encoded sequence bytes (shared store-wide)

// Lazy-load the wasm module the same way fastaDigestWorker does (dynamic import
// + default() init), which is the pattern Vite is already configured for here.
let gtars = null;
async function initWasm() {
  if (gtars) return gtars;
  const mod = await import('@databio/gtars');
  await mod.default();
  gtars = mod;
  return gtars;
}

const OPFS_DIR = "refget"; // OPFS subdir holding cached .seq files
// Probed when the manifest doesn't list collection-alias namespaces.
// Missing ones just 404/403 and are skipped.
const DEFAULT_COLLECTION_NAMESPACES = ["genome_assembly", "name", "accession", "refseq", "insdc"];
const PROGRESS_EVERY = 5000; // emit compute progress every N results
const RESULT_BATCH = 2000; // flush results to the main thread every N rows

let wasmReady = false;
let storeMeta = null; // { base, seqTemplate, collTemplate } after prepare-store
let genome = null; // { base, seqTemplate, digest, label, byName, byDigest } after select-genome
let residentStore = null; // wasm RefgetStore; grows as chromosomes are loaded
let loaded = null; // Set of sha512t24u digests already ingested

function post(msg, transfer) {
  self.postMessage(msg, transfer || []);
}
function workerLog(text, error = false) {
  post({ type: "log", text, error });
}

self.addEventListener("message", async (ev) => {
  const msg = ev.data;
  try {
    if (!wasmReady) {
      await initWasm();
      wasmReady = true;
    }
    if (msg.type === "prepare-store") {
      await prepareStore(msg.url);
    } else if (msg.type === "select-genome") {
      await selectGenome(msg.digest, msg.label);
    } else if (msg.type === "select-cached-genome") {
      await selectCachedGenome(msg.key);
    } else if (msg.type === "inspect-genome") {
      await inspectGenome(msg.key);
    } else if (msg.type === "process-vcf") {
      await processVcf(msg.buffer, msg.isGz, msg.name);
    } else if (msg.type === "process-hgvs") {
      await processHgvs(msg.lines);
    } else if (msg.type === "list-cache") {
      await listCache();
    } else if (msg.type === "delete-genome") {
      await deleteGenome(msg.key);
    } else if (msg.type === "delete-unattributed") {
      await deleteUnattributed();
    } else if (msg.type === "purge-cache") {
      await purgeCache();
    }
  } catch (err) {
    post({ type: "error", text: String(err && err.stack ? err.stack : err) });
  }
});

// ===========================================================================
// (1) Prepare store: read the manifest + collection aliases and return the list
//     of genomes (collections). No sequence bytes, no per-genome index yet.
// ===========================================================================
async function prepareStore(baseUrl) {
  const base = baseUrl.replace(/\/+$/, ""); // strip trailing slashes

  let persisted = false;
  if (navigator.storage && navigator.storage.persist) {
    persisted = await navigator.storage.persist();
  }
  if (navigator.storage && navigator.storage.estimate) {
    const est = await navigator.storage.estimate();
    post({ type: "storage-estimate", usage: est.usage, quota: est.quota, persisted });
  }

  workerLog(`Fetching ${base}/rgstore.json …`);
  const manifest = await fetchJson(`${base}/rgstore.json`);
  const seqTemplate = manifest.seqdata_path_template || "sequences/%s2/%s.seq";
  const collTemplate = manifest.collections_path_template || "collections/%s.rgsi";
  const collIndexName = manifest.collection_index || "collections.rgci";
  const namespaces =
    manifest.collection_alias_namespaces && manifest.collection_alias_namespaces.length
      ? manifest.collection_alias_namespaces
      : DEFAULT_COLLECTION_NAMESPACES;

  // n_sequences per collection (first two columns of the collection index).
  const nSeq = new Map();
  try {
    const rgci = await (await fetchOk(`${base}/${collIndexName}`)).text();
    for (const line of rgci.split("\n")) {
      if (!line || line.charCodeAt(0) === 35 /* '#' */) continue;
      const c = line.split("\t");
      if (c.length >= 2) nSeq.set(c[0], parseInt(c[1], 10));
    }
  } catch {
    /* collection index optional; selector still works from aliases */
  }

  // Collection aliases: digest -> { aliases:[...], byNs:{ ns:[...] } }.
  const byDigestLabels = new Map();
  let nsLoaded = 0;
  for (const ns of namespaces) {
    let txt;
    try {
      txt = await (await fetchOk(`${base}/aliases/collections/${ns}.tsv`)).text();
    } catch {
      continue; // namespace file not served
    }
    nsLoaded++;
    for (const line of txt.split("\n")) {
      if (!line || line.charCodeAt(0) === 35 /* '#' */) continue;
      const tab = line.indexOf("\t");
      if (tab < 0) continue;
      const alias = line.slice(0, tab).trim();
      const digest = line.slice(tab + 1).trim();
      if (!alias || !digest) continue;
      let e = byDigestLabels.get(digest);
      if (!e) {
        e = { aliases: [], byNs: {} };
        byDigestLabels.set(digest, e);
      }
      e.aliases.push(alias);
      (e.byNs[ns] ||= []).push(alias);
    }
  }

  // One entry per collection — union of those with aliases and those in the
  // index. Aliasless collections still appear (selectable by digest).
  const allDigests = new Set([...nSeq.keys(), ...byDigestLabels.keys()]);
  const genomes = [];
  for (const digest of allDigests) {
    const e = byDigestLabels.get(digest) || { aliases: [], byNs: {} };
    const assembly = e.byNs.genome_assembly ? e.byNs.genome_assembly[0] : null;
    const name = e.byNs.name ? e.byNs.name[0] : null;
    const primary = assembly || name || e.aliases[0] || digest;
    genomes.push({
      digest,
      primary,
      assembly,
      name,
      aliases: e.aliases,
      nSeq: nSeq.has(digest) ? nSeq.get(digest) : null,
    });
  }
  genomes.sort((a, b) => a.primary.localeCompare(b.primary));

  storeMeta = { base, seqTemplate, collTemplate };
  // A new store invalidates any prior selection.
  genome = null;
  residentStore = null;
  loaded = null;

  // Remember this store so it can be re-opened later from the local list.
  try {
    const root = await navigator.storage.getDirectory();
    const dir = await root.getDirectoryHandle(OPFS_DIR, { create: true });
    const stores = await readStores(dir);
    stores[base] = { label: deriveLabel(base), genomeCount: genomes.length };
    await writeStores(dir, stores);
  } catch {
    /* store-remembering is best-effort */
  }

  post({ type: "store-ready", base, genomes });
  workerLog(
    `Store has ${genomes.length} genome(s) (${nsLoaded} alias namespace(s)). ` +
      `Select one to continue.`
  );
}

// ===========================================================================
// (1b) Select a single genome (collection): load ITS sequence index. From here
//      on, every name resolves exactly within this genome — no guessing.
// ===========================================================================
async function selectGenome(digest, label) {
  if (!storeMeta) throw new Error("Store not prepared. Load a store first.");
  const base = storeMeta.base;

  workerLog(`Loading genome "${label}" (${digest}) …`);
  const rgsiUrl = `${base}/${expandTemplate(storeMeta.collTemplate, digest)}`;
  const rgsiText = await (await fetchOk(rgsiUrl)).text();

  const byName = new Map();
  const byDigest = new Map();
  for (const s of parseRgsi(rgsiText)) {
    // Within a single collection, sequence names are unique — no collisions.
    byName.set(s.name, s);
    byDigest.set(s.sha512t24u, s);
  }
  if (byName.size === 0) throw new Error("Collection index listed no sequences.");

  genome = { base, seqTemplate: storeMeta.seqTemplate, digest, label, byName, byDigest };
  residentStore = new gtars.RefgetStore();
  loaded = new Set();

  await registerGenome(digest, base, label, byDigest);

  post({ type: "genome-ready", label, digest, sequences: byName.size });
  workerLog(
    `Genome "${label}" ready: ${byName.size} sequences. Chromosome names resolve ` +
      `EXACTLY within this genome (no chr-prefix or alias guessing).`
  );
}

// Re-activate a genome already in the local store, without going through the
// store-load + pick flow. The registry remembers each genome's store base URL;
// we re-read that store's manifest for the path templates, then select the
// collection normally (its cached .seq files are reused).
async function selectCachedGenome(key) {
  const root = await navigator.storage.getDirectory();
  const dir = await root.getDirectoryHandle(OPFS_DIR, { create: true });
  const reg = await readRegistry(dir);
  const info = reg[key];
  if (!info || !info.base) {
    throw new Error("Genome not found in local store (or it predates store tracking).");
  }
  const base = info.base.replace(/\/+$/, "");
  workerLog(`Re-reading ${base}/rgstore.json for "${info.label || key}" …`);
  const manifest = await fetchJson(`${base}/rgstore.json`);
  storeMeta = {
    base,
    seqTemplate: manifest.seqdata_path_template || "sequences/%s2/%s.seq",
    collTemplate: manifest.collections_path_template || "collections/%s.rgsi",
  };
  await selectGenome(key, info.label || key);
}

// Return a genome's full sequence list (name/length/alphabet/digest) so the user
// can see exactly which names their variants must use. The active genome is
// served from memory (offline); any other cached genome is read from its
// collection index.
async function inspectGenome(key) {
  if (genome && genome.digest === key) {
    const sequences = [...genome.byName.values()].map((m) => ({
      name: m.name,
      length: m.length,
      alphabet: m.alphabet,
      sha512t24u: m.sha512t24u,
    }));
    post({ type: "genome-info", key, label: genome.label, base: genome.base, sequences });
    return;
  }
  const root = await navigator.storage.getDirectory();
  const dir = await root.getDirectoryHandle(OPFS_DIR, { create: true });
  const reg = await readRegistry(dir);
  const info = reg[key];
  if (!info || !info.base) {
    throw new Error("Genome not found in local store (or it predates store tracking).");
  }
  const base = info.base.replace(/\/+$/, "");
  const manifest = await fetchJson(`${base}/rgstore.json`);
  const collTemplate = manifest.collections_path_template || "collections/%s.rgsi";
  const rgsiText = await (await fetchOk(`${base}/${expandTemplate(collTemplate, key)}`)).text();
  const sequences = parseRgsi(rgsiText).map((m) => ({
    name: m.name,
    length: m.length,
    alphabet: m.alphabet,
    sha512t24u: m.sha512t24u,
  }));
  post({ type: "genome-info", key, label: info.label || key, base, sequences });
}

// Resolve a chromosome name strictly within the selected genome: exact match
// only. Returns the seqMeta, or null if this genome has no such sequence.
function resolveChrom(name) {
  return genome.byName.get(name) || null;
}

// Ensure the sequence for `seqMeta` is resident in the wasm store, downloading
// its encoded .seq (OPFS-cached) on first use. Returns bytes downloaded (0 if
// already loaded).
async function ensureChromLoaded(dir, seqMeta) {
  if (loaded.has(seqMeta.sha512t24u)) return 0;
  const cacheName = `${seqMeta.sha512t24u}.seq`;
  const seqUrl = `${genome.base}/${expandTemplate(genome.seqTemplate, seqMeta.sha512t24u)}`;
  const { bytes, cached } = await ensureCached(dir, cacheName, seqUrl);

  if (isEncodedAlphabet(seqMeta.alphabet)) {
    residentStore.add_encoded_sequence(
      seqMeta.name,
      seqMeta.sha512t24u,
      seqMeta.md5,
      seqMeta.length,
      bytes,
      seqMeta.alphabet
    );
  } else {
    residentStore.add_sequence(seqMeta.name, bytes);
  }
  loaded.add(seqMeta.sha512t24u);
  workerLog(
    `Loaded ${seqMeta.name} (${seqMeta.length} bp, ${seqMeta.alphabet})` +
      `${cached ? " from local storage" : " — downloaded"}.`
  );
  return cached ? 0 : bytes.byteLength;
}

// ===========================================================================
// (2) Process a VCF: scan its chromosomes, lazily load just those, then compute.
// ===========================================================================
async function processVcf(buffer, isGz, name) {
  if (!genome) {
    throw new Error("No genome selected. Pick a genome first.");
  }

  let text;
  if (isGz) {
    const ds = new DecompressionStream("gzip");
    const stream = new Blob([buffer]).stream().pipeThrough(ds);
    text = await new Response(stream).text();
  } else {
    text = new TextDecoder().decode(buffer);
  }

  const chroms = scanVcfChroms(text);
  workerLog(`VCF references ${chroms.size} distinct chromosome(s).`);

  const root = await navigator.storage.getDirectory();
  const dir = await root.getDirectoryHandle(OPFS_DIR, { create: true });

  let downloaded = 0;
  const missing = [];
  for (const c of chroms) {
    const meta = resolveChrom(c);
    if (!meta) {
      missing.push(c);
      continue;
    }
    downloaded += await ensureChromLoaded(dir, meta);
    post({ type: "download-progress", received: downloaded, total: null });
  }
  if (missing.length) {
    workerLog(
      `${missing.length} chromosome(s) are not in genome "${genome.label}" and were ` +
        `skipped: ${missing.slice(0, 10).join(", ")}${missing.length > 10 ? " …" : ""}`,
      true
    );
  }

  workerLog(`Running VRS compute over ${name} …`);
  let batch = [];
  let processed = 0;
  const onResult = (chrom, pos, ref, alt, vrsId) => {
    batch.push([chrom, pos, ref, alt, vrsId]);
    processed++;
    if (batch.length >= RESULT_BATCH) {
      post({ type: "results", rows: batch });
      batch = [];
    }
    if (processed % PROGRESS_EVERY === 0) {
      post({ type: "compute-progress", processed, total: null });
    }
  };

  const count = gtars.vcf_to_vrs_ids(residentStore, text, onResult);

  if (batch.length) post({ type: "results", rows: batch });
  post({ type: "compute-progress", processed: count, total: count });
  post({ type: "compute-done" });
  workerLog(`Computed ${count} VRS ids for ${name}.`);
}

// Convert a batch of HGVS expressions (one per line) against the selected
// genome, lazily loading whichever chromosomes they reference. Emits results as
// [hgvs, vrs_id] rows (bad/unconvertible lines get an "ERROR: …" id).
async function processHgvs(lines) {
  if (!genome) {
    throw new Error("No genome selected. Pick a genome first.");
  }
  const root = await navigator.storage.getDirectory();
  const dir = await root.getDirectoryHandle(OPFS_DIR, { create: true });

  const accessions = new Set();
  for (const line of lines) {
    try {
      const p = gtars.parse_hgvs(line);
      if (p && p.accession) accessions.add(p.accession);
    } catch {
      /* unparseable; per-line conversion reports it */
    }
  }
  let downloaded = 0;
  const missing = [];
  for (const acc of accessions) {
    const meta = resolveChrom(acc);
    if (!meta) {
      missing.push(acc);
      continue;
    }
    downloaded += await ensureChromLoaded(dir, meta);
    post({ type: "download-progress", received: downloaded, total: null });
  }
  if (missing.length) {
    workerLog(
      `Reference(s) not in genome "${genome.label}" (these HGVS lines will error): ` +
        `${missing.slice(0, 10).join(", ")}`,
      true
    );
  }

  let batch = [];
  let processed = 0;
  for (const line of lines) {
    let row;
    try {
      row = [line, residentStore.hgvs_to_vrs_id(line)];
    } catch (e) {
      row = [line, `ERROR: ${String(e && e.message ? e.message : e)}`];
    }
    batch.push(row);
    processed++;
    if (batch.length >= RESULT_BATCH) {
      post({ type: "results", rows: batch });
      batch = [];
    }
    if (processed % PROGRESS_EVERY === 0) {
      post({ type: "compute-progress", processed, total: lines.length });
    }
  }
  if (batch.length) post({ type: "results", rows: batch });
  post({ type: "compute-progress", processed: lines.length, total: lines.length });
  post({ type: "compute-done" });
  workerLog(`Converted ${lines.length} HGVS expression(s).`);
}

// Distinct CHROM values (column 0) across all non-header VCF rows.
function scanVcfChroms(text) {
  const set = new Set();
  let lineStart = 0;
  const len = text.length;
  while (lineStart < len) {
    let nl = text.indexOf("\n", lineStart);
    if (nl === -1) nl = len;
    if (text.charCodeAt(lineStart) !== 35 /* '#' */ && nl > lineStart) {
      const tab = text.indexOf("\t", lineStart);
      if (tab !== -1 && tab < nl) set.add(text.slice(lineStart, tab));
    }
    lineStart = nl + 1;
  }
  return set;
}

// ===========================================================================
// (2b) Local genome store: inventory grouped BY GENOME (collection), not by file.
// ===========================================================================
const REGISTRY_FILE = "genomes.json";
const STORES_FILE = "stores.json";

// Friendly label for a store, derived from its URL's last path segment.
function deriveLabel(base) {
  const parts = base.split("/").filter((p) => p && !p.endsWith(":"));
  return parts[parts.length - 1] || base;
}

async function readStores(dir) {
  try {
    const fh = await dir.getFileHandle(STORES_FILE, { create: false });
    const f = await fh.getFile();
    return JSON.parse(await f.text());
  } catch {
    return {};
  }
}

async function writeStores(dir, stores) {
  const fh = await dir.getFileHandle(STORES_FILE, { create: true });
  const access = await fh.createSyncAccessHandle();
  try {
    const bytes = new TextEncoder().encode(JSON.stringify(stores));
    access.truncate(0);
    access.write(bytes, { at: 0 });
    access.flush();
  } finally {
    access.close();
  }
}

async function storageEstimate() {
  if (navigator.storage && navigator.storage.estimate) {
    const e = await navigator.storage.estimate();
    return { usage: e.usage, quota: e.quota };
  }
  return { usage: null, quota: null };
}

async function readRegistry(dir) {
  try {
    const fh = await dir.getFileHandle(REGISTRY_FILE, { create: false });
    const f = await fh.getFile();
    return JSON.parse(await f.text());
  } catch {
    return {};
  }
}

async function writeRegistry(dir, reg) {
  const fh = await dir.getFileHandle(REGISTRY_FILE, { create: true });
  const access = await fh.createSyncAccessHandle();
  try {
    const bytes = new TextEncoder().encode(JSON.stringify(reg));
    access.truncate(0);
    access.write(bytes, { at: 0 });
    access.flush();
  } finally {
    access.close();
  }
}

// Register the selected genome keyed by its collection digest, so the cache
// panel groups downloaded .seq files by the genome they belong to.
async function registerGenome(collDigest, base, label, byDigest) {
  const root = await navigator.storage.getDirectory();
  const dir = await root.getDirectoryHandle(OPFS_DIR, { create: true });
  const reg = await readRegistry(dir);
  const digests = [...new Set([...byDigest.values()].map((m) => m.sha512t24u))];
  reg[collDigest] = { base, label, digests };
  await writeRegistry(dir, reg);
}

async function listCache() {
  const est = await storageEstimate();
  const root = await navigator.storage.getDirectory();
  let dir;
  try {
    dir = await root.getDirectoryHandle(OPFS_DIR, { create: false });
  } catch {
    post({ type: "genome-list", genomes: [], stores: [], other: { count: 0, bytes: 0 }, totalBytes: 0, ...est });
    return;
  }

  const sizes = new Map();
  let totalBytes = 0;
  for await (const [name, handle] of dir.entries()) {
    if (handle.kind !== "file" || !name.endsWith(".seq")) continue;
    const f = await handle.getFile();
    sizes.set(name, f.size);
    totalBytes += f.size;
  }

  const reg = await readRegistry(dir);
  const attributed = new Set();
  const genomes = [];
  for (const [key, info] of Object.entries(reg)) {
    let cachedCount = 0;
    let cachedBytes = 0;
    for (const d of info.digests) {
      const fn = `${d}.seq`;
      if (sizes.has(fn)) {
        cachedCount++;
        cachedBytes += sizes.get(fn);
        attributed.add(fn);
      }
    }
    genomes.push({
      key,
      base: info.base || key,
      label: info.label || key,
      cachedCount,
      totalCount: info.digests.length,
      cachedBytes,
      active: genome && genome.digest === key,
    });
  }

  let otherCount = 0;
  let otherBytes = 0;
  for (const [fn, sz] of sizes) {
    if (!attributed.has(fn)) {
      otherCount++;
      otherBytes += sz;
    }
  }

  genomes.sort((a, b) => b.cachedBytes - a.cachedBytes);

  // Stores: remembered stores, unioned with any store referenced by a genome.
  const storesReg = await readStores(dir);
  const storeMap = new Map();
  for (const [base, info] of Object.entries(storesReg)) {
    storeMap.set(base, {
      base,
      label: info.label || deriveLabel(base),
      genomeCount: info.genomeCount ?? null,
    });
  }
  for (const info of Object.values(reg)) {
    if (info.base && !storeMap.has(info.base)) {
      storeMap.set(info.base, { base: info.base, label: deriveLabel(info.base), genomeCount: null });
    }
  }
  const stores = [...storeMap.values()].sort((a, b) => a.label.localeCompare(b.label));

  post({ type: "genome-list", genomes, stores, other: { count: otherCount, bytes: otherBytes }, totalBytes, ...est });
}

async function deleteGenome(key) {
  const root = await navigator.storage.getDirectory();
  const dir = await root.getDirectoryHandle(OPFS_DIR, { create: false });
  const reg = await readRegistry(dir);
  const info = reg[key];
  if (!info) {
    await listCache();
    return;
  }
  // Keep any digest still referenced by another registered genome (collections
  // share sequences by digest).
  const keep = new Set();
  for (const [k, i] of Object.entries(reg)) {
    if (k !== key) for (const d of i.digests) keep.add(d);
  }
  let removed = 0;
  for (const d of info.digests) {
    if (keep.has(d)) continue;
    try {
      await dir.removeEntry(`${d}.seq`);
      removed++;
    } catch {
      /* not cached */
    }
    if (loaded) loaded.delete(d);
  }
  delete reg[key];
  await writeRegistry(dir, reg);
  workerLog(`Deleted genome "${info.label || key}" (${removed} chromosome file(s)) from local storage.`);
  await listCache();
}

async function deleteUnattributed() {
  const root = await navigator.storage.getDirectory();
  const dir = await root.getDirectoryHandle(OPFS_DIR, { create: false });
  const reg = await readRegistry(dir);
  const known = new Set();
  for (const info of Object.values(reg)) for (const d of info.digests) known.add(`${d}.seq`);

  const toDelete = [];
  for await (const [name, handle] of dir.entries()) {
    if (handle.kind === "file" && name.endsWith(".seq") && !known.has(name)) toDelete.push(name);
  }
  let removed = 0;
  for (const name of toDelete) {
    try {
      await dir.removeEntry(name);
      removed++;
      if (loaded) loaded.delete(name.replace(/\.seq$/, ""));
    } catch {
      /* ignore */
    }
  }
  workerLog(`Deleted ${removed} unattributed chromosome file(s) from local storage.`);
  await listCache();
}

async function purgeCache() {
  const root = await navigator.storage.getDirectory();
  try {
    await root.removeEntry(OPFS_DIR, { recursive: true });
  } catch {
    /* dir may not exist yet */
  }
  if (loaded) loaded.clear();
  workerLog("Deleted all genomes from local storage.");
  await listCache();
}

// ===========================================================================
// (3) OPFS cache: read a .seq if present, else download and write it.
// ===========================================================================
async function ensureCached(dir, name, url) {
  const existing = await tryReadOpfs(dir, name);
  if (existing && existing.byteLength > 0) return { bytes: existing, cached: true };
  const resp = await fetchOk(url);
  const bytes = new Uint8Array(await resp.arrayBuffer());
  await writeOpfs(dir, name, bytes);
  return { bytes, cached: false };
}

async function tryReadOpfs(dir, name) {
  try {
    const fh = await dir.getFileHandle(name, { create: false });
    const access = await fh.createSyncAccessHandle();
    try {
      const size = access.getSize();
      const buf = new Uint8Array(size);
      access.read(buf, { at: 0 });
      return buf;
    } finally {
      access.close();
    }
  } catch {
    return null; // NotFoundError → not cached yet
  }
}

async function writeOpfs(dir, name, bytes) {
  const fh = await dir.getFileHandle(name, { create: true });
  const access = await fh.createSyncAccessHandle();
  try {
    access.truncate(0);
    access.write(bytes, { at: 0 });
    access.flush();
  } finally {
    access.close();
  }
}

// ===========================================================================
// (4) refgetstore format + fetch helpers
// ===========================================================================
function expandTemplate(template, digest) {
  return template
    .replaceAll("%s2", digest.slice(0, 2))
    .replaceAll("%s4", digest.slice(0, 4))
    .replaceAll("%s", digest);
}

function parseRgsi(text) {
  const out = [];
  for (const line of text.split("\n")) {
    if (line.length === 0 || line.charCodeAt(0) === 35 /* '#' */) continue;
    const c = line.split("\t");
    if (c.length < 5) continue;
    out.push({ name: c[0], length: parseInt(c[1], 10), alphabet: c[2], sha512t24u: c[3], md5: c[4] });
  }
  return out;
}

function isEncodedAlphabet(alphabet) {
  const a = alphabet.toLowerCase();
  return a === "dna2bit" || a === "dna3bit" || a === "dnaio" || a === "dnaiupac";
}

async function fetchOk(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`fetch ${url} → HTTP ${resp.status}`);
  return resp;
}
async function fetchJson(url) {
  return (await fetchOk(url)).json();
}
