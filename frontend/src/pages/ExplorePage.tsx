import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { API_BASE } from '../utilities';
import stores from '../data/stores.json';
import { Icon } from '../components/common/Icon';

const CopyableUrl = ({ url, label = 'URL' }: { url: string; label?: string }) => {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      timer.current = setTimeout(() => setCopied(false), 1200);
    } catch {
      toast.error('Failed to copy to clipboard');
    }
  };
  return (
    <span className="inline-flex items-center gap-1">
      <code className="code text-xs text-muted text-break">{url}</code>
      <button
        type="button"
        className="btn--link text-muted"
        onClick={copy}
        title={copied ? 'Copied!' : `Copy ${label}`}
        aria-label={`Copy ${label}`}
      >
        <Icon name={copied ? 'check' : 'clipboard'} />
      </button>
      <span className="sr-only" role="status" aria-live="polite">
        {copied ? `${label} copied` : ''}
      </span>
    </span>
  );
};

// The hero store (the flagship hosted SeqCol API); falls back to the first.
const heroStore = stores.find((s) => s.hero) || stores[0];
// Other (non-hero) stores that also expose a hosted SeqCol API.
const otherApiStores = stores.filter((s) => s.api && !s.hero);

const ExplorePage = () => {
  const jungleStoreUrl = heroStore.url;

  // Live collection counts per store, from each store's public collections.rgci.
  // url -> count, null on error, absent while loading.
  const [counts, setCounts] = useState<Record<string, number | null>>({});
  useEffect(() => {
    let cancelled = false;
    stores.forEach(async (s) => {
      try {
        const res = await fetch(`${s.url}collections.rgci`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const text = await res.text();
        const n = text.split('\n').filter((l) => l && !l.startsWith('#')).length;
        if (!cancelled) setCounts((c) => ({ ...c, [s.url]: n }));
      } catch {
        if (!cancelled) setCounts((c) => ({ ...c, [s.url]: null }));
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const fmtCount = (url: string) => {
    const v = counts[url];
    if (v === undefined) return '…';
    if (v === null) return '—';
    return v.toLocaleString();
  };

  return (
    <div className="mb-12">
      {/* LOCAL TOOLS */}
      <h4 className="font-light mb-4">
        <Icon name="tools" className="mr-2" />
        Local Tools
      </h4>
      <p className="text-muted text-sm mb-4">Work offline, no server needed.</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
        <div>
          <div className="card h-full">
            <div className="card__body">
              <h6 className="card__title">
                <Link to="/fasta" className="no-underline">
                  <Icon name="arrow-right" className="mr-2" />
                  FASTA Digester
                </Link>
              </h6>
              <p className="card__text text-muted text-sm mb-0">
                Compute sequence collection digests from FASTA files in-browser.
              </p>
            </div>
          </div>
        </div>
        <div>
          <div className="card h-full">
            <div className="card__body">
              <h6 className="card__title">
                <Link to="/vrs" className="no-underline">
                  <Icon name="arrow-right" className="mr-2" />
                  VCF / HGVS → VRS
                </Link>
              </h6>
              <p className="card__text text-muted text-sm mb-0">
                Convert variants to GA4GH VRS allele IDs in-browser.
              </p>
            </div>
          </div>
        </div>
        <div>
          <div className="card h-full">
            <div className="card__body">
              <h6 className="card__title">
                <Link to="/compare" className="no-underline">
                  <Icon name="arrow-right" className="mr-2" />
                  Compare (SCIM)
                </Link>
              </h6>
              <p className="card__text text-muted text-sm mb-0">
                Interpret and visualize sequence collection comparisons.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* SEQCOL API (hero — the one hosted API server, backed by the jungle store) */}
      <h4 className="font-light mb-4">
        <Icon name="network" className="mr-2" />
        SeqCol API Servers
      </h4>
      <p className="text-muted text-sm mb-4">
        Hosted Sequence Collections API servers. The flagship is backed by the Reference Genome
        Jungle store; a second instance backs the Demo store as an always-green GA4GH compliance
        reference.
      </p>

      <div className="card mb-12">
        <div className="card__header">
          <h5 className="mb-0">
            {heroStore.name}
            <span className="badge badge--success ml-2">API</span>
          </h5>
        </div>
        <div className="card__body">
          <p className="text-muted text-sm mb-4">
            A curated collection of human (GRCh38/hg19/hg18) and mouse (mm39 and earlier) reference assemblies
            from many authorities — UCSC, Ensembl, GENCODE, NCBI, iGenomes, refgenie, ENA, DDBJ, and others —
            so you can compare how the same genome is represented across providers.
          </p>
          <div className="mb-4">
            <div className="flex items-center mb-1">
              <span className="badge badge--success mr-2">API</span>
              <strong className="text-sm">Sequence Collections API:</strong>
              <span className="ml-2"><CopyableUrl url={heroStore.api ?? ''} label="API base URL" /></span>
            </div>
            <div className="flex items-center mb-1">
              <span className="badge badge--secondary mr-2">Store</span>
              <strong className="text-sm">Store:</strong>
              <span className="ml-2"><CopyableUrl url={jungleStoreUrl} label="store URL" /></span>
            </div>
            <div className="text-muted text-sm mt-2">{fmtCount(jungleStoreUrl)} collections</div>
          </div>

          <div className="mb-4">
            <Link to="/jungle" className="btn btn--outline-primary">
              <Icon name="tree" className="mr-2" />
              Browse with Provenance
            </Link>
          </div>

          {/* The card describes heroStore from stores.json, but the "Browse via
              API" links below resolve through API_BASE. In production these are
              the same server; anywhere else, say so rather than silently
              browsing a different one than the card advertises. */}
          {API_BASE !== heroStore.api && (
            <div className="alert alert--warning py-2 text-sm mb-4">
              This build is connected to <code>{API_BASE}</code>, so the “Browse via API” links
              below query that server, not the one listed above.
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h6 className="text-muted text-sm uppercase mb-2">Browse via API</h6>
              <ul className="list-unstyled mb-0">
                <li className="mb-1">
                  <Link to="/collections" className="no-underline text-sm">
                    <Icon name="arrow-right" className="mr-1" />Collections
                  </Link>
                </li>
                <li className="mb-1">
                  <Link to="/sequences" className="no-underline text-sm">
                    <Icon name="arrow-right" className="mr-1" />Sequences
                  </Link>
                </li>
                <li className="mb-1">
                  <Link to="/aliases" className="no-underline text-sm">
                    <Icon name="arrow-right" className="mr-1" />Aliases
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h6 className="text-muted text-sm uppercase mb-2">Views</h6>
              <ul className="list-unstyled mb-0">
                <li className="mb-1">
                  <Link to="/human" className="no-underline text-sm">
                    <Icon name="arrow-right" className="mr-1" />Human Genomes
                  </Link>
                </li>
                <li className="mb-1">
                  <Link to="/scom" className="no-underline text-sm">
                    <Icon name="arrow-right" className="mr-1" />SCOM
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h6 className="text-muted text-sm uppercase mb-2">Developer</h6>
              <ul className="list-unstyled mb-0">
                <li className="mb-1">
                  <a href={`${heroStore.api}/docs`} className="no-underline text-sm" target="_blank" rel="noopener noreferrer">
                    <Icon name="arrow-right" className="mr-1" />API Docs
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Additional API servers (e.g. the demo / compliance-reference instance) */}
      {otherApiStores.map((s) => (
        <div className="card mb-12" key={s.api}>
          <div className="card__header">
            <h5 className="mb-0">
              {s.name}
              <span className="badge badge--success ml-2">API</span>
            </h5>
          </div>
          <div className="card__body">
            <p className="text-muted text-sm mb-4">{s.description}</p>
            <div className="mb-4">
              <div className="flex items-center mb-1">
                <span className="badge badge--success mr-2">API</span>
                <strong className="text-sm">Sequence Collections API:</strong>
                <span className="ml-2"><CopyableUrl url={s.api ?? ''} label="API base URL" /></span>
              </div>
              <div className="flex items-center mb-1">
                <span className="badge badge--secondary mr-2">Store</span>
                <strong className="text-sm">Store:</strong>
                <span className="ml-2"><CopyableUrl url={s.url} label="store URL" /></span>
              </div>
              <div className="text-muted text-sm mt-2">{fmtCount(s.url)} collections</div>
            </div>
            <div>
              <a
                href={`${s.api}/docs`}
                className="btn btn--outline-primary btn--sm mr-2"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Icon name="external" className="mr-1" />
                API docs
              </a>
              <Link
                to={`/compliance?url=${encodeURIComponent(s.api ?? '')}`}
                className="btn btn--outline-success btn--sm"
              >
                <Icon name="check-circle" className="mr-1" />
                Run compliance
              </Link>
            </div>
          </div>
        </div>
      ))}

      {/* REFGETSTORES (table of all published stores, from src/data/stores.json) */}
      <h4 className="font-light mb-4">
        <Icon name="archive" className="mr-2" />
        RefgetStores
      </h4>
      <p className="text-muted text-sm mb-4">
        All publicly published RefgetStores. Browse any of them in the store explorer (read directly from S3,
        no server required). Stores marked <span className="badge badge--success">API</span> also have a hosted
        SeqCol API.
      </p>

      <div className="table-wrap mb-6">
        <table className="table table--sm align-middle">
          <thead>
            <tr>
              <th>Store</th>
              <th>Description</th>
              <th className="text-right">Collections</th>
              <th>URL</th>
              <th>Access</th>
            </tr>
          </thead>
          <tbody>
            {stores.map((s) => (
              <tr key={s.url}>
                <td className="font-medium text-nowrap">
                  {s.name}
                  {s.api && <span className="badge badge--success ml-2">API</span>}
                </td>
                <td className="text-muted text-sm">{s.description}</td>
                <td className="text-right">{fmtCount(s.url)}</td>
                <td><CopyableUrl url={s.url} label="store URL" /></td>
                <td className="text-nowrap text-sm">
                  <Link to={`/explore-store/overview?url=${encodeURIComponent(s.url)}`}>
                    Browse store
                  </Link>
                  {s.api && (
                    <>
                      {' · '}
                      <a href={`${s.api}/docs`} target="_blank" rel="noopener noreferrer">
                        API docs
                      </a>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Work with any store / API by URL */}
      <div className="card">
        <div className="card__header">
          <h5 className="mb-0">Explore any store or API by URL</h5>
        </div>
        <div className="card__body">
          <ul className="list-unstyled mb-0">
            <li className="mb-2">
              <Link to="/explore-store" className="no-underline text-sm">
                <Icon name="arrow-right" className="mr-1" />Explore a Store
              </Link>
              <span className="text-muted block text-sm ml-4">Browse any RefgetStore by URL</span>
            </li>
            <li className="mb-2">
              <Link to="/explore-api" className="no-underline text-sm">
                <Icon name="arrow-right" className="mr-1" />Explore an API
              </Link>
              <span className="text-muted block text-sm ml-4">Connect to any SeqCol API server</span>
            </li>
            <li>
              <Link to="/compliance" className="no-underline text-sm">
                <Icon name="arrow-right" className="mr-1" />Compliance Testing
              </Link>
              <span className="text-muted block text-sm ml-4">Run GA4GH spec compliance checks</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export { ExplorePage };
