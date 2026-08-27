import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import type { CSSProperties } from 'react';
import toast from 'react-hot-toast';
import { BaseModal } from '../components/common/BaseModal';

/** One selectable genome (collection) in a store. */
interface GenomeOption {
  digest: string;
  primary: string;
  assembly?: string | null;
  name?: string | null;
  aliases: string[];
  nSeq?: number | null;
}

/** A genome's sequence list, as returned by the worker's inspect-genome. */
interface InspectedSequence {
  name: string;
  length: number;
  alphabet: string;
  sha512t24u: string;
}

/** What the genome inspector modal renders. */
interface GenomeInfo {
  key: string;
  label: string;
  base: string;
  sequences?: InspectedSequence[];
}

/** One cached genome in the local (OPFS) store panel. */
interface CachedGenome {
  key: string;
  base: string;
  label: string;
  cachedCount: number;
  totalCount: number;
  cachedBytes: number;
  active: boolean;
}

/** The worker's cache inventory. */
interface CacheReport {
  genomes: CachedGenome[];
  stores: Array<{ base: string; label: string; genomeCount: number | null }>;
  other: { count: number; bytes: number };
  totalBytes: number;
  usage?: number | null;
  quota?: number | null;
}

/** One line of the on-page worker log. */
interface LogLine {
  t: string;
  text: string;
  isError: boolean;
}

// Default demo store: the public `jungle` refgetstore on S3. A store holds MANY
// genomes (collections); the user picks exactly one, and names then resolve only
// within that genome — no assembly ambiguity. Any served gtars refgetstore works.
const STORE_EXAMPLE = 'https://refgenie.s3.us-east-1.amazonaws.com/refget-store/jungle';
// Examples use UCSC-style names (chr20/chrM); they only resolve if you select a
// genome that uses those names (e.g. a UCSC hg38). Pick the matching genome.
const VCF_EXAMPLE =
  '##fileformat=VCFv4.2\n' +
  '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n' +
  'chrM\t100\t.\tA\tG\t.\t.\t.\n' +
  'chr20\t5000000\t.\tC\tT\t.\t.\t.\n';
const HGVS_EXAMPLE = 'chrM:g.100A>G\nchr20:g.5000000C>T';

const VCF_HEADER = ['chrom', 'pos', 'ref', 'alt', 'vrs_id'];
const HGVS_HEADER = ['hgvs', 'vrs_id'];
const MAX_PREVIEW = 200;

function fmtBytes(n: number | null | undefined) {
  if (n == null) return '?';
  const u = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  let value = n;
  while (value >= 1024 && i < u.length - 1) {
    value /= 1024;
    i++;
  }
  return `${value.toFixed(i === 0 ? 0 : 1)} ${u[i]}`;
}

function createWorker() {
  return new Worker(new URL('../components/vrs/vrsWorker.ts', import.meta.url), {
    type: 'module',
  });
}

// Type-filtered genome picker. Filters across every alias (genome_assembly,
// name, accession, …) so "hg38", "GRCh38", or "GCF_000001405.39" all find it.
interface GenomeSelectProps {
  genomes: GenomeOption[];
  selected: GenomeOption | null;
  onSelect: (genome: GenomeOption) => void;
  disabled?: boolean;
}

function GenomeSelect({ genomes, selected, onSelect, disabled }: GenomeSelectProps) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const blurTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    const haystack = (g: GenomeOption) =>
      [g.primary, g.assembly, g.name, ...(g.aliases || [])]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
    const list = q ? genomes.filter((g) => haystack(g).includes(q)) : genomes;
    return list.slice(0, 50);
  }, [genomes, query]);

  const pick = (g: GenomeOption) => {
    onSelect(g);
    setQuery('');
    setOpen(false);
  };

  return (
    <div className="relative">
      <input
        type="text"
        className="form-input"
        placeholder={
          selected
            ? `Selected: ${selected.primary} — type to change`
            : `Type to filter ${genomes.length} genome(s): hg38, GRCh38, GCF_…`
        }
        value={query}
        disabled={disabled}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          // delay so a click on an option registers before we close
          blurTimer.current = setTimeout(() => setOpen(false), 150);
        }}
      />
      {open && matches.length > 0 && (
        <ul
          className="list-group genome-suggestions w-full shadow-sm"
          onMouseDown={() => clearTimeout(blurTimer.current)}
        >
          {matches.map((g) => (
            <li key={g.digest}>
              <button
                type="button"
                className={`list-group__item list-group__item--action w-full text-left ${
 selected && selected.digest === g.digest ? 'list-group__item--current' : ''
 }`}
                onClick={() => pick(g)}
              >
                <span className="font-semibold">{g.primary}</span>
                {g.nSeq != null && (
                  <span className="badge badge--secondary text-muted ml-2">
                    {g.nSeq} seqs
                  </span>
                )}
                {g.aliases && g.aliases.length > 1 && (
                  <div className="text-sm text-muted font-mono text-truncate">
                    {g.aliases.filter((a) => a !== g.primary).join(' · ')}
                  </div>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// Modal listing a genome's sequence names so the user knows exactly which names
// their VCF / HGVS must use. Filterable; names are copyable.
function GenomeInspector({ info, onClose }: { info: GenomeInfo; onClose: () => void }) {
  const [q, setQ] = useState('');
  const filtered = useMemo(() => {
    const seqs = info.sequences || [];
    const needle = q.trim().toLowerCase();
    return needle
      ? seqs.filter((s: InspectedSequence) => s.name.toLowerCase().includes(needle))
      : seqs;
  }, [info.sequences, q]);

  const copyNames = async () => {
    try {
      await navigator.clipboard.writeText(
        filtered.map((s: InspectedSequence) => s.name).join('\n'),
      );
      toast.success(`Copied ${filtered.length} name(s)`);
    } catch {
      toast.error('Copy failed');
    }
  };

  return (
    <BaseModal isOpen onClose={onClose} title={`Genome: ${info.label}`} size="lg">
      <div className="text-sm text-muted font-mono text-break mb-4">{info.base}</div>
      {!info.sequences ? (
        <div className="text-muted">Loading sequence list…</div>
      ) : (
        <>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              className="form-input form-input--sm"
              placeholder="Filter names…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              autoFocus
            />
            <button
              className="btn btn--sm btn--outline-secondary text-nowrap"
              onClick={copyNames}
            >
              Copy names
            </button>
          </div>
          <div className="text-sm text-muted mb-2">
            {filtered.length.toLocaleString()} of {info.sequences.length.toLocaleString()}{' '}
            sequence(s). Use these <strong>exact</strong> names as the CHROM / accession
            in your input.
          </div>
          <table className="table table--sm table--striped font-mono text-sm mb-0">
            <thead>
              <tr><th>name</th><th className="text-right">length</th><th>alphabet</th></tr>
            </thead>
            <tbody>
              {filtered.map((s: InspectedSequence) => (
                <tr key={s.name}>
                  <td>{s.name}</td>
                  <td className="text-right">{s.length.toLocaleString()}</td>
                  <td className="text-muted">{s.alphabet}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </BaseModal>
  );
}

export function VrsConverter() {
  const [storeUrl, setStoreUrl] = useState('');
  const [loadingStore, setLoadingStore] = useState(false);
  const [genomes, setGenomes] = useState<GenomeOption[]>([]);
  const [selected, setSelected] = useState<GenomeOption | null>(null);
  const [selecting, setSelecting] = useState(false);
  const [genomeReady, setGenomeReady] = useState(false);
  const [genomeInfo, setGenomeInfo] = useState('');

  const [inputMode, setInputMode] = useState('vcf-file');
  const [vcfText, setVcfText] = useState('');
  const [hgvsText, setHgvsText] = useState('');

  const [header, setHeader] = useState(VCF_HEADER);
  const [preview, setPreview] = useState<string[][]>([]);
  const [computeInfo, setComputeInfo] = useState('');
  const [computeFrac, setComputeFrac] = useState(0);
  const [running, setRunning] = useState(false);
  const [resultCount, setResultCount] = useState(0);

  const [cache, setCache] = useState<CacheReport | null>(null);
  const [inspect, setInspect] = useState<GenomeInfo | null>(null);
  const [log, setLog] = useState<LogLine[]>([]);

  const workerRef = useRef<Worker | null>(null);
  const allRowsRef = useRef<string[][]>([]);
  const headerRef = useRef<string[]>(VCF_HEADER);
  const startTsRef = useRef(0);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const addLog = useCallback((text: string, isError = false) => {
    setLog((prev) => [
      ...prev.slice(-200),
      { t: new Date().toLocaleTimeString(), text, isError },
    ]);
  }, []);

  const requestCacheList = useCallback(() => {
    workerRef.current?.postMessage({ type: 'list-cache' });
  }, []);

  useEffect(() => {
    const worker = createWorker();
    worker.onmessage = (e: MessageEvent) => {
      const msg = e.data;
      switch (msg.type) {
        case 'log':
          addLog(msg.text, !!msg.error);
          break;
        case 'storage-estimate':
          break;
        case 'store-ready':
          setLoadingStore(false);
          setGenomes(msg.genomes);
          setSelected(null);
          setGenomeReady(false);
          setGenomeInfo(
            `Store has ${msg.genomes.length} genome(s). Select one below.`
          );
          toast.success(`Loaded store — ${msg.genomes.length} genomes`);
          break;
        case 'genome-ready':
          setSelecting(false);
          setGenomeReady(true);
          setGenomeInfo(
            `Active genome: ${msg.label} — ${msg.sequences ?? '?'} sequences. ` +
              `Names resolve exactly within this genome.`
          );
          toast.success(`Genome ready: ${msg.label}`);
          requestCacheList();
          break;
        case 'download-progress':
          setGenomeInfo(`Downloading chromosomes… ${fmtBytes(msg.received)}`);
          break;
        case 'results':
          allRowsRef.current.push(...msg.rows);
          if (allRowsRef.current.length <= MAX_PREVIEW || preview.length < MAX_PREVIEW) {
            setPreview(allRowsRef.current.slice(0, MAX_PREVIEW));
          }
          break;
        case 'compute-progress': {
          const frac = msg.total ? msg.processed / msg.total : 0;
          setComputeFrac(frac);
          const elapsed = (performance.now() - startTsRef.current) / 1000;
          const rate = msg.processed / Math.max(elapsed, 0.001);
          setComputeInfo(
            `${msg.processed.toLocaleString()}` +
              (msg.total ? ` / ${msg.total.toLocaleString()}` : '') +
              ` (${rate.toFixed(0)}/s)`
          );
          break;
        }
        case 'compute-done':
          setRunning(false);
          setComputeFrac(1);
          setResultCount(allRowsRef.current.length);
          setPreview(allRowsRef.current.slice(0, MAX_PREVIEW));
          setComputeInfo(
            `Done: ${allRowsRef.current.length.toLocaleString()} results in ` +
              `${((performance.now() - startTsRef.current) / 1000).toFixed(1)}s.`
          );
          requestCacheList();
          break;
        case 'genome-list':
          setCache(msg);
          break;
        case 'genome-info':
          setInspect(msg);
          break;
        case 'error':
          setRunning(false);
          setLoadingStore(false);
          setSelecting(false);
          addLog(msg.text, true);
          toast.error('Error — see log');
          break;
        default:
          break;
      }
    };
    worker.onerror = (ev) => {
      ev.preventDefault();
      addLog(ev.message || 'Worker crashed', true);
      setRunning(false);
      setLoadingStore(false);
      setSelecting(false);
    };
    workerRef.current = worker;
    requestCacheList();
    return () => worker.terminate();
  }, [addLog, requestCacheList]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadStoreUrl = (url: string) => {
    setStoreUrl(url);
    setLoadingStore(true);
    setGenomes([]);
    setSelected(null);
    setGenomeReady(false);
    setGenomeInfo('Reading store…');
    workerRef.current?.postMessage({ type: 'prepare-store', url });
  };

  const loadStore = () => {
    const url = storeUrl.trim();
    if (!url) {
      toast.error('Enter a refgetstore URL');
      return;
    }
    loadStoreUrl(url);
  };

  const onSelectGenome = (g: GenomeOption) => {
    setSelected(g);
    setSelecting(true);
    setGenomeReady(false);
    setGenomeInfo(`Loading ${g.primary}…`);
    workerRef.current?.postMessage({ type: 'select-genome', digest: g.digest, label: g.primary });
  };

  const resetResults = (hdr: string[]) => {
    headerRef.current = hdr;
    setHeader(hdr);
    allRowsRef.current = [];
    setPreview([]);
    setResultCount(0);
    setComputeFrac(0);
    setComputeInfo('');
    setRunning(true);
    startTsRef.current = performance.now();
  };

  const requireGenome = () => {
    if (!genomeReady) {
      toast.error('Select a genome first');
      return false;
    }
    return true;
  };

  const onVcfFile = async (file: File | null | undefined) => {
    if (!file || !requireGenome()) return;
    resetResults(VCF_HEADER);
    const isGz = /\.gz$/i.test(file.name);
    addLog(`Loaded "${file.name}" (${fmtBytes(file.size)})${isGz ? ' — gzip' : ''}.`);
    const buf = await file.arrayBuffer();
    workerRef.current?.postMessage(
      { type: 'process-vcf', buffer: buf, isGz, name: file.name },
      [buf]
    );
  };

  const runVcfPaste = () => {
    if (!requireGenome()) return;
    if (!vcfText.trim()) {
      toast.error('Paste some VCF text');
      return;
    }
    resetResults(VCF_HEADER);
    const buf = new TextEncoder().encode(vcfText).buffer;
    workerRef.current?.postMessage(
      { type: 'process-vcf', buffer: buf, isGz: false, name: 'pasted.vcf' },
      [buf]
    );
  };

  const runHgvs = () => {
    if (!requireGenome()) return;
    const lines = hgvsText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    if (lines.length === 0) {
      toast.error('Enter at least one HGVS expression');
      return;
    }
    resetResults(HGVS_HEADER);
    workerRef.current?.postMessage({ type: 'process-hgvs', lines });
  };

  const downloadTsv = () => {
    const lines = [headerRef.current.join('\t')];
    for (const r of allRowsRef.current) lines.push(r.join('\t'));
    const blob = new Blob([lines.join('\n') + '\n'], {
      type: 'text/tab-separated-values',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vrs_results.tsv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const inspectGenome = (g: CachedGenome) => {
    setInspect({ key: g.key, label: g.label, base: g.base }); // open with loading state
    workerRef.current?.postMessage({ type: 'inspect-genome', key: g.key });
  };
  const loadCachedGenome = (g: CachedGenome) => {
    setSelected(null);
    setGenomeReady(false);
    setStoreUrl(g.base);
    setGenomeInfo(`Loading ${g.label}…`);
    workerRef.current?.postMessage({ type: 'select-cached-genome', key: g.key });
  };
  const deleteGenome = (g: CachedGenome) => {
    if (window.confirm(`Delete genome "${g.label}" (${fmtBytes(g.cachedBytes)}) from local storage?`)) {
      workerRef.current?.postMessage({ type: 'delete-genome', key: g.key });
    }
  };
  const deleteUnattributed = (other: { count: number; bytes: number }) => {
    if (window.confirm(`Delete ${other.count} unattributed file(s) (${fmtBytes(other.bytes)})?`)) {
      workerRef.current?.postMessage({ type: 'delete-unattributed' });
    }
  };
  const purgeAll = () => {
    if (window.confirm('Delete ALL downloaded chromosomes from local storage?')) {
      workerRef.current?.postMessage({ type: 'purge-cache' });
    }
  };

  return (
    <div className="py-6">
      <h2 className="mb-1">HGVS / VCF → VRS</h2>
      <p className="text-muted">
        Convert variants — a VCF file, pasted VCF, or HGVS expressions — into GA4GH{' '}
        <code>ga4gh:VA.&lt;digest&gt;</code> allele identifiers, entirely in your browser.
        Pick one reference genome; it is downloaded once and cached locally; nothing is
        sent to a server.
      </p>

      {/* 1. Genome */}
      <div className="card mb-4">
        <div className="card__body">
          <h5 className="card__title">1. Reference genome</h5>

          {/* 1a. Store URL */}
          <label className="form-label text-sm text-muted mb-1">Store URL</label>
          <div className="input-group">
            <input
              type="text"
              className="form-input font-mono"
              placeholder="https://…/refget-store/…"
              value={storeUrl}
              onChange={(e) => setStoreUrl(e.target.value)}
            />
            <button className="btn btn--outline-secondary" onClick={() => setStoreUrl(STORE_EXAMPLE)}>
              Use example
            </button>
            <button className="btn btn--primary" onClick={loadStore} disabled={loadingStore}>
              {loadingStore ? 'Loading…' : 'Load store'}
            </button>
          </div>
          <div className="form-hint">
            URL of a hosted gtars refgetstore. Loading reads only small index files and
            lists the genomes it contains.
          </div>

          {/* 1b. Genome picker */}
          {genomes.length > 0 && (
            <div className="mt-4">
              <label className="form-label text-sm text-muted mb-1">
                Genome ({genomes.length} available)
              </label>
              <GenomeSelect
                genomes={genomes}
                selected={selected}
                onSelect={onSelectGenome}
                disabled={selecting}
              />
              <div className="form-hint">
                Pick exactly one genome. Chromosome names in your input must match this
                genome&apos;s names exactly — no guessing across assemblies.
              </div>
            </div>
          )}

          {genomeInfo && (
            <div className={`text-sm mt-2 ${genomeReady ? 'text-success-fg' : 'text-muted'}`}>{genomeInfo}</div>
          )}
        </div>
      </div>

      {/* 2. Input */}
      <div className="card mb-4">
        <div className="card__body">
          <h5 className="card__title">2. Input</h5>
          <div className="btn-group mb-4" role="group" aria-label="Input mode">
            {[
              ['vcf-file', 'VCF file'],
              ['vcf-paste', 'VCF (paste)'],
              ['hgvs', 'HGVS'],
            ].map(([mode, label]) => (
              <button
                key={mode}
                type="button"
                className={`btn btn--sm text-nowrap ${inputMode === mode ? 'btn--primary' : 'btn--outline-primary'}`}
                onClick={() => setInputMode(mode)}
              >
                {label}
              </button>
            ))}
          </div>

          {inputMode === 'vcf-file' && (
            <div
              className="border border-2 border-muted rounded p-6 text-center text-muted cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (e.dataTransfer.files?.[0]) onVcfFile(e.dataTransfer.files[0]);
              }}
            >
              Drag &amp; drop a <code>.vcf</code> / <code>.vcf.gz</code> here, or click to pick
              <input
                ref={fileInputRef}
                type="file"
                accept=".vcf,.vcf.gz,.gz"
                hidden
                onChange={(e) => e.target.files?.[0] && onVcfFile(e.target.files[0])}
              />
            </div>
          )}

          {inputMode === 'vcf-paste' && (
            <div>
              <textarea
                className="form-input font-mono"
                rows={6}
                placeholder="#CHROM&#9;POS&#9;ID&#9;REF&#9;ALT&#9;…"
                value={vcfText}
                onChange={(e) => setVcfText(e.target.value)}
              />
              <div className="mt-2">
                <button className="btn btn--sm btn--outline-secondary mr-2" onClick={() => setVcfText(VCF_EXAMPLE)}>
                  Load example
                </button>
                <button className="btn btn--sm btn--primary" onClick={runVcfPaste} disabled={running}>
                  Convert
                </button>
              </div>
            </div>
          )}

          {inputMode === 'hgvs' && (
            <div>
              <textarea
                className="form-input font-mono"
                rows={6}
                placeholder="chrM:g.100A>G"
                value={hgvsText}
                onChange={(e) => setHgvsText(e.target.value)}
              />
              <div className="form-hint">
                One genomic (<code>g.</code>) HGVS expression per line. HGVS validates the
                stated reference base against the genome.
              </div>
              <div className="mt-2">
                <button className="btn btn--sm btn--outline-secondary mr-2" onClick={() => setHgvsText(HGVS_EXAMPLE)}>
                  Load example
                </button>
                <button className="btn btn--sm btn--primary" onClick={runHgvs} disabled={running}>
                  Convert
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Results */}
      <div className="card mb-4">
        <div className="card__body">
          <div className="flex justify-between items-center mb-2">
            <h5 className="card__title mb-0">3. Results</h5>
            <button
              className="btn btn--sm btn--outline-primary"
              onClick={downloadTsv}
              disabled={resultCount === 0}
            >
              Download TSV
            </button>
          </div>
          {(running || computeInfo) && (
            <>
              <div className="progress progress--sm mb-1">
                <div
                  className="progress__bar"
                  style={{ '--progress-value': `${computeFrac * 100}%` } as CSSProperties}
                />
              </div>
              <div className="text-sm text-muted mb-2">{computeInfo}</div>
            </>
          )}
          {preview.length === 0 ? (
            <div className="text-muted text-sm">No results yet.</div>
          ) : (
            <div className="table-wrap">
              <table className="table table--sm table--striped font-mono text-sm mb-0">
                <thead>
                  <tr>{header.map((h) => <th key={h}>{h}</th>)}</tr>
                </thead>
                <tbody>
                  {preview.map((r, i) => (
                    <tr key={i}>
                      {r.map((c, j) => <td key={j}>{String(c)}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
              {resultCount > preview.length && (
                <div className="text-sm text-muted mt-1">
                  Showing first {preview.length.toLocaleString()} of{' '}
                  {resultCount.toLocaleString()} — download the TSV for all.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 4. Local storage */}
      <div className="card mb-4">
        <div className="card__body">
          <div className="flex justify-between items-center mb-2">
            <h5 className="card__title mb-0">Local storage</h5>
            <div>
              <button className="btn btn--sm btn--outline-secondary mr-2" onClick={requestCacheList}>
                Refresh
              </button>
              <button className="btn btn--sm btn--outline-danger" onClick={purgeAll}>
                Delete all
              </button>
            </div>
          </div>
          {cache && (
            <div className="text-sm text-muted mb-2">
              {cache.genomes.length} genome(s), {fmtBytes(cache.totalBytes)} saved locally
              {cache.quota != null && ` · browser storage: ${fmtBytes(cache.usage)} / ${fmtBytes(cache.quota)}`}
            </div>
          )}

          {/* Stores: re-open a whole store to pick a (different) genome from it */}
          <h6 className="text-muted mt-2">Stores</h6>
          <div className="table-wrap mb-4">
            <table className="table table--sm align-middle mb-0">
              <thead>
                <tr><th>store</th><th>genomes</th><th></th></tr>
              </thead>
              <tbody>
                {(!cache || cache.stores?.length === 0) && (
                  <tr><td colSpan={3} className="text-muted text-sm">No stores loaded yet.</td></tr>
                )}
                {cache?.stores?.map((s) => (
                  <tr key={s.base}>
                    <td>
                      {s.label}
                      {storeUrl.trim().replace(/\/+$/, '') === s.base && (
                        <span className="badge badge--primary text-primary-fg ml-2">open</span>
                      )}
                      <div className="text-sm text-muted font-mono text-break">{s.base}</div>
                    </td>
                    <td className="text-sm">{s.genomeCount ?? '?'}</td>
                    <td>
                      <button className="btn btn--sm btn--outline-primary" onClick={() => loadStoreUrl(s.base)} disabled={loadingStore}>
                        Load this store
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Genomes: jump straight to a single downloaded genome */}
          <h6 className="text-muted">Genomes</h6>
          <div className="table-wrap">
            <table className="table table--sm align-middle mb-0">
              <thead>
                <tr><th>genome</th><th>chromosomes</th><th>size</th><th></th></tr>
              </thead>
              <tbody>
                {(!cache || (cache.genomes.length === 0 && cache.other.count === 0)) && (
                  <tr><td colSpan={4} className="text-muted text-sm">No genomes downloaded yet.</td></tr>
                )}
                {cache?.genomes.map((g) => (
                  <tr key={g.key}>
                    <td>{g.label}{g.active && <span className="badge badge--success text-success-fg ml-2">active</span>}</td>
                    <td className="text-sm">{g.cachedCount} / {g.totalCount}</td>
                    <td className="text-sm">{fmtBytes(g.cachedBytes)}</td>
                    <td>
                      {g.key !== g.base && (
                        <button className="btn btn--sm btn--outline-secondary mr-2" onClick={() => inspectGenome(g)}>
                          Inspect
                        </button>
                      )}
                      {!g.active && g.key !== g.base && (
                        <button className="btn btn--sm btn--outline-primary mr-2" onClick={() => loadCachedGenome(g)}>
                          Load this genome
                        </button>
                      )}
                      {g.cachedCount > 0 && (
                        <button className="btn btn--sm btn--outline-danger" onClick={() => deleteGenome(g)}>
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {(cache?.other.count ?? 0) > 0 && cache && (
                  <tr>
                    <td className="text-muted text-sm">(unattributed — from an earlier download)</td>
                    <td className="text-sm">{cache.other.count} files</td>
                    <td className="text-sm">{fmtBytes(cache.other.bytes)}</td>
                    <td>
                      <button className="btn btn--sm btn--outline-danger" onClick={() => deleteUnattributed(cache.other)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Log */}
      <details>
        <summary className="text-muted text-sm">Log</summary>
        <pre className="log-panel mt-2">
          {log.map((l, i) => (
            <div key={i} className={l.isError ? 'text-danger-fg' : ''}>
              {l.t}  {l.text}
            </div>
          ))}
        </pre>
      </details>

      {inspect && <GenomeInspector info={inspect} onClose={() => setInspect(null)} />}
    </div>
  );
}
