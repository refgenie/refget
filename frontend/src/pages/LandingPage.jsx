import { Link, useOutletContext } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore.js';
import { CopyableDigest } from '../components/CopyableDigest.jsx';
import { useEffect } from 'react';

const LandingPage = () => {
  const { apiAvailable } = useOutletContext();
  const { hasStore, hasAPI, storeUrl, storeMetadata, storeCollections, serviceInfo, probe, probed } =
    useUnifiedStore();

  useEffect(() => {
    if (!probed) probe();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const nCollections = storeCollections?.length || serviceInfo?.seqcol?.refget_store?.n_collections;
  const nSequences = serviceInfo?.seqcol?.refget_store?.n_sequences || storeMetadata?.n_sequences;
  const aliasNamespaces = storeMetadata?.collection_alias_namespaces || serviceInfo?.seqcol?.refget_store?.collection_alias_namespaces || [];
  const scomEnabled = serviceInfo?.seqcol?.scom?.enabled;

  return (
    <div className="mb-5">
      <h3 className="fw-light mb-4">Refget Sequence Collections</h3>

      <p>
        Welcome to the Refget Sequence Collections service. Browse, compare, and
        explore reference genome sequence collections following the{' '}
        <a
          href="https://ga4gh.github.io/refget/"
          target="_blank"
          rel="noopener noreferrer"
        >
          GA4GH refget specification
        </a>.
      </p>

      <div className="row g-4 mt-3">
        {/* Browse section */}
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="bi bi-collection me-2" />
                Browse
              </h5>
            </div>
            <div className="card-body">
              <p className="text-muted small mb-3">
                Explore sequence collections on this server. Each collection represents a reference genome assembly with its sequences, names, and lengths.
              </p>
              {storeUrl && (
                <div className="mb-3 d-flex align-items-center">
                  <small className="text-muted me-2">Store:</small>
                  <span style={{ fontSize: '0.7rem', fontFamily: '"Roboto Condensed", "Arial Narrow", "Helvetica Neue", Arial, sans-serif', fontStretch: 'condensed', wordBreak: 'break-all' }}>
                    <CopyableDigest value={storeUrl} />
                  </span>
                </div>
              )}
              <ul className="list-unstyled mb-0">
                <li className="mb-2">
                  <Link to="/collections" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    Collections
                    {nCollections && <span className="text-muted ms-1">(n = {Number(nCollections).toLocaleString()})</span>}
                  </Link>
                </li>
                <li className="mb-2">
                  <Link to="/sequences" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    Sequences
                    {nSequences && <span className="text-muted ms-1">(n = {Number(nSequences).toLocaleString()})</span>}
                  </Link>
                </li>
                <li className="mb-2">
                  <Link to="/aliases" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    Aliases
                    {aliasNamespaces.length > 0 && (
                      <span className="text-muted ms-1">
                        ({aliasNamespaces.length} namespace{aliasNamespaces.length !== 1 ? 's' : ''}: {aliasNamespaces.join(', ')})
                      </span>
                    )}
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Tools section */}
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="bi bi-tools me-2" />
                Tools
              </h5>
            </div>
            <div className="card-body">
              <p className="text-muted small mb-3">
                Standalone tools for working with sequence collections. Compute digests, compare assemblies, or connect to external servers.
              </p>
              <ul className="list-unstyled mb-0">
                <li className="mb-2">
                  <Link to="/fasta" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    FASTA Digester
                  </Link>
                  <span className="text-muted d-block small ms-4">
                    Compute digests from FASTA files in-browser
                  </span>
                </li>
                <li className="mb-2">
                  <Link to="/compare" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    Compare (SCIM)
                  </Link>
                  <span className="text-muted d-block small ms-4">
                    Interpret sequence collection comparisons
                  </span>
                </li>
                <li className="mb-2">
                  <Link to="/explore-store" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    Explore a Store
                  </Link>
                  <span className="text-muted d-block small ms-4">
                    Browse any RefgetStore by URL
                  </span>
                </li>
                <li className="mb-2">
                  <Link to="/explore-api" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    Explore an API
                  </Link>
                  <span className="text-muted d-block small ms-4">
                    Connect to any SeqCol API server
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="row g-4 mt-1">
        {/* Curated section */}
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="bi bi-bookmark-star me-2" />
                Curated
              </h5>
            </div>
            <div className="card-body">
              <p className="text-muted small mb-3">
                Pre-built views for specific genome sets. Precomputed similarity matrices and curated reference genome pages.
              </p>
              <ul className="list-unstyled mb-0">
                {scomEnabled && (
                  <li className="mb-2">
                    <Link to="/scom" className="text-decoration-none">
                      <i className="bi bi-arrow-right me-2" />
                      SCOM — Similarity Matrix
                    </Link>
                  </li>
                )}
                <li className="mb-2">
                  <Link to="/human" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    Human Reference Genomes
                  </Link>
                </li>
                <li className="mb-2">
                  <Link to="/hprc" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    HPRC Genomes
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="bi bi-check-circle me-2" />
                Developer
              </h5>
            </div>
            <div className="card-body">
              <p className="text-muted small mb-3">
                Test API compliance and explore the raw API endpoints. For developers building on the seqcol specification.
              </p>
              <ul className="list-unstyled mb-0">
                <li className="mb-2">
                  <Link to="/compliance" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    Compliance Testing
                  </Link>
                  <span className="text-muted d-block small ms-4">
                    Run GA4GH spec compliance checks
                  </span>
                </li>
                <li className="mb-2">
                  <Link to="/demo" className="text-decoration-none">
                    <i className="bi bi-arrow-right me-2" />
                    Demo
                  </Link>
                  <span className="text-muted d-block small ms-4">
                    Collection comparison demo
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {!apiAvailable && (
        <div className="alert alert-warning mt-4">
          <i className="bi bi-exclamation-triangle me-2" />
          The API is currently unavailable. Some features may be limited.
        </div>
      )}
    </div>
  );
};

export { LandingPage };
