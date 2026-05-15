import { Link } from 'react-router-dom';

import ga4gh_logo from '../assets/ga4gh-logo.png';
import python_logo from '../assets/logo_python.svg';
import refget_logo from '../assets/refget_logo.svg';
import seqcol_logo from '../assets/seqcol_logo.svg';

const LandingPage = () => {
  return (
    <div className="mb-5">
      <div className="text-center mb-5">
        <img src={seqcol_logo} alt="Refget" height="80" className="mb-3" />
        <h2 className="fw-light mb-3">Refget Sequence Collections</h2>
        <p className="lead text-muted mx-auto" style={{ maxWidth: '700px' }}>
          Refget is a set of GA4GH standards for identifying and distributing
          reference biological sequences. Sequence collections provide a way to
          represent, compare, and retrieve sets of sequences, like reference genomes, using
          content-derived identifiers.
        </p>
      </div>

      <div className="row g-4 justify-content-center">
        {/* The Specification */}
        <div className="col-md-3">
          <a
            href="https://ga4gh.github.io/refget/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-decoration-none"
          >
            <div className="card h-100 text-center border-0 shadow-sm hover-shadow">
              <div className="card-body py-5">
                <img src={ga4gh_logo} alt="GA4GH" height="60" className="mb-4" />
                <h4 className="card-title">The Specification</h4>
                <p className="card-text text-muted">
                  Read the GA4GH specification for refget sequences and sequence collections.
                </p>
              </div>
            </div>
          </a>
        </div>

        {/* Python Package */}
        <div className="col-md-3">
          <a
            href="https://refgenie.org/refget/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-decoration-none"
          >
            <div className="card h-100 text-center border-0 shadow-sm hover-shadow">
              <div className="card-body py-5">
                <div className="mb-4" style={{ height: '60px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                  <img src={refget_logo} alt="Refget" height="50" />
                  <img src={python_logo} alt="Python" height="30" />
                </div>
                <h4 className="card-title">Python Package</h4>
                <p className="card-text text-muted">
                  Compute digests, compare collections, and interact with APIs using Python.
                </p>
              </div>
            </div>
          </a>
        </div>

        {/* Try it Live */}
        <div className="col-md-3">
          <Link to="/explore" className="text-decoration-none">
            <div className="card h-100 text-center border-0 shadow-sm hover-shadow">
              <div className="card-body py-5">
                <i className="bi bi-play-circle fs-1 text-primary mb-3 d-block" style={{ height: '60px', lineHeight: '60px' }}></i>
                <h4 className="card-title">Try it Live</h4>
                <p className="card-text text-muted">
                  Browse sequence collections on this server.
                </p>
              </div>
            </div>
          </Link>
        </div>

        {/* The Jungle */}
        <div className="col-md-3">
          <Link to="/jungle" className="text-decoration-none">
            <div className="card h-100 text-center border-0 shadow-sm hover-shadow">
              <div className="card-body py-5">
                <span className="fs-1 mb-3 d-block" style={{ height: '60px', lineHeight: '60px' }}>🧬</span>
                <h4 className="card-title">The Jungle</h4>
                <p className="card-text text-muted">
                  100+ reference genomes with provenance.
                </p>
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* How should I use this? */}
      <div className="mt-5 pt-4 border-top">
        <h5 className="fw-light text-center mb-4">How should I use this?</h5>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>

          {/* Header row */}
          <div className="row g-0 pb-2 mb-2 border-bottom">
            <div className="col-md-5 pe-3 text-end">
              <strong className="text-muted small text-uppercase">Are you...</strong>
            </div>
            <div className="col-md-7 ps-3 border-start">
              <strong className="text-muted small text-uppercase">Then...</strong>
            </div>
          </div>

          <div className="row g-0 py-2">
            <div className="col-md-5 pe-3 text-end">
              <i className="bi bi-journal-text me-2 text-primary" />
              Publishing data aligned to a reference?
            </div>
            <div className="col-md-7 ps-3 border-start text-muted">
              Publish the unambiguous refget digest to identify the reference you used. Use the <Link to="/fasta">FASTA Digester</Link> or <Link to="/collections">browse known references</Link>.
            </div>
          </div>

          <div className="row g-0 py-2">
            <div className="col-md-5 pe-3 text-end">
              <i className="bi bi-collection me-2 text-primary" />
              Looking for available reference genomes?
            </div>
            <div className="col-md-7 ps-3 border-start text-muted">
              <Link to="/jungle">Browse the Jungle</Link> to find GRCh38, T2T-CHM13, and 100+ references with provenance and source links.
            </div>
          </div>

          <div className="row g-0 py-2">
            <div className="col-md-5 pe-3 text-end">
              <i className="bi bi-arrow-left-right me-2 text-primary" />
              Comparing your reference against known genomes?
            </div>
            <div className="col-md-7 ps-3 border-start text-muted">
              Use <Link to="/scom">SCOM</Link> to compare your local reference against human, mouse, and other genomes on the server.
            </div>
          </div>

          <div className="row g-0 py-2">
            <div className="col-md-5 pe-3 text-end">
              <i className="bi bi-search me-2 text-primary" />
              Trying to identify an unknown FASTA?
            </div>
            <div className="col-md-7 ps-3 border-start text-muted">
              Use the <Link to="/fasta">FASTA Digester</Link> to compute a digest, then <Link to="/scom">compare</Link> to find matches.
            </div>
          </div>

          <div className="row g-0 py-2">
            <div className="col-md-5 pe-3 text-end">
              <i className="bi bi-file-text me-2 text-primary" />
              Have comparison output to interpret?
            </div>
            <div className="col-md-7 ps-3 border-start text-muted">
              Use <Link to="/compare">SCIM</Link> to get a human-friendly interpretation of comparison results.
            </div>
          </div>

          <div className="row g-0 py-2">
            <div className="col-md-5 pe-3 text-end">
              <i className="bi bi-list-ol me-2 text-primary" />
              Referring to sequences without names?
            </div>
            <div className="col-md-7 ps-3 border-start text-muted">
              Use <code>sorted_sequences</code> to identify sequences regardless of names or order.
            </div>
          </div>

          <div className="row g-0 py-2">
            <div className="col-md-5 pe-3 text-end">
              <i className="bi bi-rulers me-2 text-primary" />
              Checking coordinate system compatibility?
            </div>
            <div className="col-md-7 ps-3 border-start text-muted">
              Compare <code>sorted_name_length_pairs</code> to check if "chr1" and "1" map to the same positions.
            </div>
          </div>

        </div>
      </div>

      <style>{`
        .hover-shadow:hover {
          box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
          transform: translateY(-2px);
          transition: all 0.2s ease-in-out;
        }
        .hover-shadow {
          transition: all 0.2s ease-in-out;
        }
      `}</style>
    </div>
  );
};

export { LandingPage };
