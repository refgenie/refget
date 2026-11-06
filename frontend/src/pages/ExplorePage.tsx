import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { API_BASE } from '../utilities';
import storeList from '../data/stores.json';
import howItFits from '../assets/how-it-fits.svg';
import { Icon } from '../components/common/Icon';

/** A published RefgetStore and what is available for it (src/data/stores.json). */
interface StoreEntry {
  name: string;
  description: string;
  /** Store base URL (the S3 prefix holding rgstore.json). */
  url: string;
  /** SeqCol API server backed by this store, if one is hosted. */
  api?: string;
  /** refgenie serves assets for genomes from this store. */
  refgenie?: boolean;
  /** Pages of this site built for this store's data. */
  views?: { label: string; to: string }[];
}

const stores: StoreEntry[] = storeList;

const REFGENIE_GENOMES_URL = 'https://api.refgenie.org/genomes';

// The Jungle views (/jungle, /human, /scom) query this build's API_BASE. In
// production that is the Jungle store's API; anywhere else, say so.
const jungle = stores.find((s) => s.views?.some((v) => v.to === '/jungle'));
const viewsUseOtherApi = Boolean(jungle?.api && jungle.api !== API_BASE);

const CopyUrlButton = ({ url, label }: { url: string; label: string }) => {
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
    <>
      <button
        type="button"
        className="btn--link text-muted ml-2"
        onClick={copy}
        title={copied ? 'Copied!' : `Copy ${label}: ${url}`}
        aria-label={`Copy ${label}`}
      >
        <Icon name={copied ? 'check' : 'clipboard'} />
      </button>
      <span className="sr-only" role="status" aria-live="polite">
        {copied ? `${label} copied` : ''}
      </span>
    </>
  );
};

const None = () => <span className="text-muted">—</span>;

const ExplorePage = () => {
  // Live collection counts per store, from each store's public collections.rgci.
  // url -> count, null on error, absent while loading.
  const [counts, setCounts] = useState<Record<string, number | null>>({});
  useEffect(() => {
    let cancelled = false;
    stores.forEach(async (s) => {
      try {
        const res = await fetch(`${s.url}collections.rgci`, { cache: 'no-cache' });
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
      {/* REFERENCE STORES: the main catalog, one row per published store */}
      <h4 className="font-light mb-4">
        <Icon name="archive" className="mr-2" />
        Reference stores
      </h4>
      <div className="explore__intro mb-4">
        <p className="text-muted text-sm mb-0">
          Each store is a published set of reference genomes. <strong>Browse</strong> opens a store
          right here, read straight from its files. Some stores also have an <strong>API</strong>, a
          web service that follows the GA4GH Sequence Collections standard, and{' '}
          <strong>refgenie</strong> serves ready-built assets (aligner indexes, annotations) for
          genomes from some stores. <strong>Views</strong> are pages on this site made for one store.
        </p>
        <img
          src={howItFits}
          className="explore__figure"
          alt="Everything is built on a store: a SeqCol API server is a store with an API on top; a refgenie server is a store with refgenie serving an API and assets on top."
        />
      </div>

      {viewsUseOtherApi && (
        <div className="alert alert--warning py-2 text-sm mb-4">
          This build is connected to <code>{API_BASE}</code>, so the Jungle views query that
          server, not <code>{jungle?.api}</code>.
        </div>
      )}

      <div className="table-wrap mb-12">
        <table className="table table--sm align-middle">
          <thead>
            <tr>
              <th>Store</th>
              <th className="text-right">Collections</th>
              <th>Browse</th>
              <th>API</th>
              <th>refgenie</th>
              <th>Views</th>
            </tr>
          </thead>
          <tbody>
            {stores.map((s) => (
              <tr key={s.url}>
                <td>
                  <div className="text-nowrap">
                    <Link
                      to={`/explore-store/overview?url=${encodeURIComponent(s.url)}`}
                      className="no-underline"
                    >
                      <strong>{s.name}</strong>
                    </Link>
                    <CopyUrlButton url={s.url} label={`${s.name} store URL`} />
                  </div>
                  <div className="text-muted">{s.description}</div>
                </td>
                <td className="text-right">{fmtCount(s.url)}</td>
                <td className="text-nowrap text-sm">
                  <Link to={`/explore-store/overview?url=${encodeURIComponent(s.url)}`}>Browse</Link>
                </td>
                <td className="text-nowrap text-sm">
                  {s.api ? (
                    <Link to={`/explore-api/collections?url=${encodeURIComponent(s.api)}`} title={s.api}>
                      API
                    </Link>
                  ) : (
                    <None />
                  )}
                </td>
                <td className="text-nowrap text-sm">
                  {s.refgenie ? (
                    <a href={REFGENIE_GENOMES_URL} target="_blank" rel="noopener noreferrer">
                      refgenie <Icon name="external" />
                    </a>
                  ) : (
                    <None />
                  )}
                </td>
                <td className="text-sm">
                  {s.views?.length ? (
                    s.views.map((v, i) => (
                      <span key={v.to} className="text-nowrap">
                        {i > 0 && ' · '}
                        <Link to={v.to}>{v.label}</Link>
                      </span>
                    ))
                  ) : (
                    <None />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

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
