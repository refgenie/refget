import { Link } from 'react-router-dom';
import { API_BASE } from '../utilities.jsx';

const CopyableUrl = ({ url }) => (
  <code
    className="small text-muted"
    style={{ fontSize: '0.75rem', wordBreak: 'break-all' }}
  >
    {url}
  </code>
);

const ExplorePage = () => {
  const jungleStoreUrl = 'https://refgenie.s3.us-east-1.amazonaws.com/refget-store/jungle/';
  const pangenomeStoreUrl = 'https://refgenie.s3.us-east-1.amazonaws.com/pangenome_refget_store';

  return (
    <div className="mb-5">
      {/* LOCAL TOOLS */}
      <h4 className="fw-light mb-3">
        <i className="bi bi-tools me-2" />
        Local Tools
      </h4>
      <p className="text-muted small mb-3">Work offline, no server needed.</p>

      <div className="row g-3 mb-5">
        <div className="col-md-6">
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
        <div className="col-md-6">
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

      {/* SERVERS */}
      <h4 className="fw-light mb-3">
        <i className="bi bi-hdd-network me-2" />
        Servers
      </h4>

      <div className="row g-4">
        {/* Jungle Server */}
        <div className="col-12">
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">The Reference Genome Jungle</h5>
            </div>
            <div className="card-body">
              <p className="text-muted small mb-3">
                A comprehensive collection of reference genomes including human assemblies (GRCh38, T2T-CHM13, HPRC pangenome),
                model organisms, and common research references. Includes precomputed similarity matrices for comparing assemblies.
              </p>
              <div className="mb-3">
                <div className="d-flex align-items-center mb-1">
                  <span className="badge bg-success me-2">API</span>
                  <strong className="small">Sequence Collections API:</strong>
                  <span className="ms-2"><CopyableUrl url="seqcolapi.databio.org" /></span>
                </div>
                <div className="d-flex align-items-center mb-1">
                  <span className="badge bg-secondary me-2">Store</span>
                  <strong className="small">Store:</strong>
                  <span className="ms-2"><CopyableUrl url={jungleStoreUrl} /></span>
                </div>
                <div className="text-muted small mt-2">
                  205 collections · 580,742 sequences
                </div>
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
                  <h6 className="text-muted small text-uppercase mb-2 mt-3">Browse Store Directly</h6>
                  <ul className="list-unstyled mb-0">
                    <li className="mb-1">
                      <Link
                        to={`/explore-store/overview?url=${encodeURIComponent(jungleStoreUrl)}`}
                        className="text-decoration-none small"
                      >
                        <i className="bi bi-arrow-right me-1" />Browse Store
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
                      <Link to="/hprc" className="text-decoration-none small">
                        <i className="bi bi-arrow-right me-1" />HPRC Genomes
                      </Link>
                    </li>
                    <li className="mb-1">
                      <Link to="/scom" className="text-decoration-none small">
                        <i className="bi bi-arrow-right me-1" />SCOM
                      </Link>
                    </li>
                    <li className="mb-1">
                      <Link to="/demo" className="text-decoration-none small">
                        <i className="bi bi-arrow-right me-1" />Demo
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
        </div>

        {/* Pangenome Store */}
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="mb-0">Pangenome</h5>
            </div>
            <div className="card-body">
              <div className="mb-3">
                <div className="d-flex align-items-center mb-1">
                  <span className="badge bg-secondary me-2">Store</span>
                  <strong className="small">Store:</strong>
                </div>
                <div className="ms-4">
                  <CopyableUrl url={pangenomeStoreUrl} />
                </div>
                <div className="text-muted small mt-2">
                  47 HPRC haplotype-resolved assemblies
                </div>
              </div>

              <ul className="list-unstyled mb-0">
                <li>
                  <Link
                    to={`/explore-store/overview?url=${encodeURIComponent(pangenomeStoreUrl)}`}
                    className="text-decoration-none small"
                  >
                    <i className="bi bi-arrow-right me-1" />Browse Store
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Work with Any Server */}
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="mb-0">Work with Any SeqCol API</h5>
            </div>
            <div className="card-body">
              <p className="text-muted small mb-3">
                Explore any Sequence Collections API or RefgetStore by URL.
              </p>

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
      </div>
    </div>
  );
};

export { ExplorePage };
