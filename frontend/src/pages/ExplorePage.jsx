import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { API_BASE } from '../utilities.jsx';
import stores from '../data/stores.json';

const CopyableUrl = ({ url }) => (
  <code
    className="small text-muted"
    style={{ fontSize: '0.75rem', wordBreak: 'break-all' }}
  >
    {url}
  </code>
);

// The hero store (the one with a hosted SeqCol API); falls back to the first.
const heroStore = stores.find((s) => s.hero) || stores[0];

const ExplorePage = () => {
  const jungleStoreUrl = heroStore.url;

  // Live collection counts per store, from each store's public collections.rgci.
  const [counts, setCounts] = useState({}); // url -> number | null (error) | undefined (loading)
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

  const fmtCount = (url) => {
    const v = counts[url];
    if (v === undefined) return '…';
    if (v === null) return '—';
    return v.toLocaleString();
  };

  return (
    <div className="mb-5">
      {/* LOCAL TOOLS */}
      <h4 className="fw-light mb-3">
        <i className="bi bi-tools me-2" />
        Local Tools
      </h4>
      <p className="text-muted small mb-3">Work offline, no server needed.</p>

      <div className="row g-3 mb-5">
        <div className="col-md-4">
          <div className="card h-100">
            <div className="card-body">
              <h6 className="card-title">
                <Link to="/fasta" className="text-decoration-none">
                  <i className="bi bi-arrow-right me-2" />
                  FASTA Digester
                </Link>
              </h6>
              <p className="card-text text-muted small mb-0">
                Compute sequence collection digests from FASTA files in-browser.
              </p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card h-100">
            <div className="card-body">
              <h6 className="card-title">
                <Link to="/vrs" className="text-decoration-none">
                  <i className="bi bi-arrow-right me-2" />
                  VCF / HGVS → VRS
                </Link>
              </h6>
              <p className="card-text text-muted small mb-0">
                Convert variants to GA4GH VRS allele IDs in-browser.
              </p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card h-100">
            <div className="card-body">
              <h6 className="card-title">
                <Link to="/compare" className="text-decoration-none">
                  <i className="bi bi-arrow-right me-2" />
                  Compare (SCIM)
                </Link>
              </h6>
              <p className="card-text text-muted small mb-0">
                Interpret and visualize sequence collection comparisons.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* SEQCOL API (hero — the one hosted API server, backed by the jungle store) */}
      <h4 className="fw-light mb-3">
        <i className="bi bi-hdd-network me-2" />
        SeqCol API
      </h4>
      <p className="text-muted small mb-3">
        The hosted Sequence Collections API, backed by the Reference Genome Jungle store.
      </p>

      <div className="card mb-5">
        <div className="card-header">
          <h5 className="mb-0">
            {heroStore.name}
            <span className="badge bg-success ms-2">API</span>
          </h5>
        </div>
        <div className="card-body">
          <p className="text-muted small mb-3">
            A curated collection of human (GRCh38/hg19/hg18) and mouse (mm39 and earlier) reference assemblies
            from many authorities — UCSC, Ensembl, GENCODE, NCBI, iGenomes, refgenie, ENA, DDBJ, and others —
            so you can compare how the same genome is represented across providers.
          </p>
          <div className="mb-3">
            <div className="d-flex align-items-center mb-1">
              <span className="badge bg-success me-2">API</span>
              <strong className="small">Sequence Collections API:</strong>
              <span className="ms-2"><CopyableUrl url={heroStore.api} /></span>
            </div>
            <div className="d-flex align-items-center mb-1">
              <span className="badge bg-secondary me-2">Store</span>
              <strong className="small">Store:</strong>
              <span className="ms-2"><CopyableUrl url={jungleStoreUrl} /></span>
            </div>
            <div className="text-muted small mt-2">{fmtCount(jungleStoreUrl)} collections</div>
          </div>

          <div className="mb-3">
            <Link to="/jungle" className="btn btn-outline-primary">
              <i className="bi bi-tree me-2" />
              Browse with Provenance
            </Link>
          </div>

          <div className="row">
            <div className="col-md-4">
              <h6 className="text-muted small text-uppercase mb-2">Browse via API</h6>
              <ul className="list-unstyled mb-0">
                <li className="mb-1">
                  <Link to="/collections" className="text-decoration-none small">
                    <i className="bi bi-arrow-right me-1" />Collections
                  </Link>
                </li>
                <li className="mb-1">
                  <Link to="/sequences" className="text-decoration-none small">
                    <i className="bi bi-arrow-right me-1" />Sequences
                  </Link>
                </li>
                <li className="mb-1">
                  <Link to="/aliases" className="text-decoration-none small">
                    <i className="bi bi-arrow-right me-1" />Aliases
                  </Link>
                </li>
              </ul>
            </div>
            <div className="col-md-4">
              <h6 className="text-muted small text-uppercase mb-2">Views</h6>
              <ul className="list-unstyled mb-0">
                <li className="mb-1">
                  <Link to="/human" className="text-decoration-none small">
                    <i className="bi bi-arrow-right me-1" />Human Genomes
                  </Link>
                </li>
                <li className="mb-1">
                  <Link to="/scom" className="text-decoration-none small">
                    <i className="bi bi-arrow-right me-1" />SCOM
                  </Link>
                </li>
              </ul>
            </div>
            <div className="col-md-4">
              <h6 className="text-muted small text-uppercase mb-2">Developer</h6>
              <ul className="list-unstyled mb-0">
                <li className="mb-1">
                  <a href={`${API_BASE}/docs`} className="text-decoration-none small" target="_blank" rel="noopener noreferrer">
                    <i className="bi bi-arrow-right me-1" />API Docs
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* REFGETSTORES (table of all published stores, from src/data/stores.json) */}
      <h4 className="fw-light mb-3">
        <i className="bi bi-archive me-2" />
        RefgetStores
      </h4>
      <p className="text-muted small mb-3">
        All publicly published RefgetStores. Browse any of them in the store explorer (read directly from S3,
        no server required). Only the jungle additionally has a hosted SeqCol API.
      </p>

      <div className="table-responsive mb-4">
        <table className="table table-sm align-middle">
          <thead>
            <tr>
              <th>Store</th>
              <th>Description</th>
              <th className="text-end">Collections</th>
              <th>Access</th>
            </tr>
          </thead>
          <tbody>
            {stores.map((s) => (
              <tr key={s.url}>
                <td className="fw-medium text-nowrap">
                  {s.name}
                  {s.api && <span className="badge bg-success ms-2">API</span>}
                </td>
                <td className="text-muted small">{s.description}</td>
                <td className="text-end">{fmtCount(s.url)}</td>
                <td className="text-nowrap small">
                  <Link to={`/explore-store/overview?url=${encodeURIComponent(s.url)}`}>
                    Browse store
                  </Link>
                  {s.api && (
                    <>
                      {' · '}
                      <a href={`https://${s.api}`} target="_blank" rel="noopener noreferrer">
                        API
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
        <div className="card-header">
          <h5 className="mb-0">Explore any store or API by URL</h5>
        </div>
        <div className="card-body">
          <ul className="list-unstyled mb-0">
            <li className="mb-2">
              <Link to="/explore-store" className="text-decoration-none small">
                <i className="bi bi-arrow-right me-1" />Explore a Store
              </Link>
              <span className="text-muted d-block small ms-3">Browse any RefgetStore by URL</span>
            </li>
            <li className="mb-2">
              <Link to="/explore-api" className="text-decoration-none small">
                <i className="bi bi-arrow-right me-1" />Explore an API
              </Link>
              <span className="text-muted d-block small ms-3">Connect to any SeqCol API server</span>
            </li>
            <li>
              <Link to="/compliance" className="text-decoration-none small">
                <i className="bi bi-arrow-right me-1" />Compliance Testing
              </Link>
              <span className="text-muted d-block small ms-3">Run GA4GH spec compliance checks</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export { ExplorePage };
