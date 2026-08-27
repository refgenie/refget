import { Link } from 'react-router-dom';

import ga4gh_logo from '../assets/ga4gh-logo.png';
import python_logo from '../assets/logo_python.svg';
import refget_logo from '../assets/refget_logo.svg';
import seqcol_logo from '../assets/seqcol_logo.svg';
import { Icon } from '../components/common/Icon';

const LandingPage = () => {
  return (
    <div className="mb-12">
      <div className="text-center mb-12">
        <img src={seqcol_logo} alt="Refget" height="80" className="mb-4" />
        <h2 className="text-3xl font-light mb-4">Refget Sequence Collections</h2>
        <p className="text-lg text-muted mx-auto landing__lede">
          Refget is a set of GA4GH standards for identifying and distributing
          reference biological sequences. Sequence collections provide a way to
          represent, compare, and retrieve sets of sequences, like reference genomes, using
          content-derived identifiers.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* The Specification */}
        <div>
          <a
            href="https://ga4gh.github.io/refget/"
            target="_blank"
            rel="noopener noreferrer"
            className="no-underline"
          >
            <div className="card h-full text-center border-0 shadow-sm card--hover">
              <div className="card__body py-12">
                <img src={ga4gh_logo} alt="GA4GH" height="60" className="mb-6" />
                <h4 className="card__title">The Specification</h4>
                <p className="card__text text-muted">
                  Read the GA4GH specification for refget sequences and sequence collections.
                </p>
              </div>
            </div>
          </a>
        </div>

        {/* Python Package */}
        <div>
          <a
            href="https://refgenie.org/refget/"
            target="_blank"
            rel="noopener noreferrer"
            className="no-underline"
          >
            <div className="card h-full text-center border-0 shadow-sm card--hover">
              <div className="card__body py-12">
                <div className="landing__logo-row mb-6">
                  <img src={refget_logo} alt="Refget" height="50" />
                  <img src={python_logo} alt="Python" height="30" />
                </div>
                <h4 className="card__title">Python Package</h4>
                <p className="card__text text-muted">
                  Compute digests, compare collections, and interact with APIs using Python.
                </p>
              </div>
            </div>
          </a>
        </div>

        {/* Try it Live */}
        <div>
          <Link to="/explore" className="no-underline">
            <div className="card h-full text-center border-0 shadow-sm card--hover">
              <div className="card__body py-12">
                <Icon name="play" className="landing__glyph text-primary-fg mb-4 block" />
                <h4 className="card__title">Try it Live</h4>
                <p className="card__text text-muted">
                  Browse sequence collections on this server.
                </p>
              </div>
            </div>
          </Link>
        </div>

        {/* The Jungle */}
        <div>
          <Link to="/jungle" className="no-underline">
            <div className="card h-full text-center border-0 shadow-sm card--hover">
              <div className="card__body py-12">
                <span className="landing__emoji text-4xl mb-4 block">🧬</span>
                <h4 className="card__title">The Jungle</h4>
                <p className="card__text text-muted">
                  100+ reference genomes with provenance.
                </p>
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* How should I use this? */}
      <div className="mt-12 pt-6 border-t border-muted">
        <h5 className="text-lg font-light text-center mb-6">How should I use this?</h5>
        <div className="guide">

          {/* Header row */}
          <div className="guide__row guide__row--head pb-2 mb-2 border-b border-muted">
            <div className="guide__ask">
              <strong className="text-muted text-sm uppercase">Are you...</strong>
            </div>
            <div className="guide__answer border-l">
              <strong className="text-muted text-sm uppercase">Then...</strong>
            </div>
          </div>

          <div className="guide__row py-2">
            <div className="guide__ask">
              <Icon name="journal" className="mr-2 text-primary-fg" />
              Publishing data aligned to a reference?
            </div>
            <div className="guide__answer border-l text-muted">
              Publish the unambiguous refget digest to identify the reference you used. Use the <Link to="/fasta">FASTA Digester</Link> or <Link to="/collections">browse known references</Link>.
            </div>
          </div>

          <div className="guide__row py-2">
            <div className="guide__ask">
              <Icon name="collection" className="mr-2 text-primary-fg" />
              Looking for available reference genomes?
            </div>
            <div className="guide__answer border-l text-muted">
              <Link to="/jungle">Browse the Jungle</Link> to find GRCh38, hg19, mouse assemblies, and 100+ human and mouse references with provenance and source links.
            </div>
          </div>

          <div className="guide__row py-2">
            <div className="guide__ask">
              <Icon name="arrow-left-right" className="mr-2 text-primary-fg" />
              Comparing your reference against known genomes?
            </div>
            <div className="guide__answer border-l text-muted">
              Use <Link to="/scom">SCOM</Link> to compare your local reference against human, mouse, and other genomes on the server.
            </div>
          </div>

          <div className="guide__row py-2">
            <div className="guide__ask">
              <Icon name="search" className="mr-2 text-primary-fg" />
              Trying to identify an unknown FASTA?
            </div>
            <div className="guide__answer border-l text-muted">
              Use the <Link to="/fasta">FASTA Digester</Link> to compute a digest, then <Link to="/scom">compare</Link> to find matches.
            </div>
          </div>

          <div className="guide__row py-2">
            <div className="guide__ask">
              <Icon name="file-text" className="mr-2 text-primary-fg" />
              Have comparison output to interpret?
            </div>
            <div className="guide__answer border-l text-muted">
              Use <Link to="/compare">SCIM</Link> to get a human-friendly interpretation of comparison results.
            </div>
          </div>

          <div className="guide__row py-2">
            <div className="guide__ask">
              <Icon name="list-ol" className="mr-2 text-primary-fg" />
              Referring to sequences without names?
            </div>
            <div className="guide__answer border-l text-muted">
              Use <code className="code code--inline">sorted_sequences</code> to identify sequences regardless of names or order.
            </div>
          </div>

          <div className="guide__row py-2">
            <div className="guide__ask">
              <Icon name="rulers" className="mr-2 text-primary-fg" />
              Checking coordinate system compatibility?
            </div>
            <div className="guide__answer border-l text-muted">
              Compare <code className="code code--inline">sorted_name_length_pairs</code> to check if &quot;chr1&quot; and &quot;1&quot; map to the same positions.
            </div>
          </div>

        </div>
      </div>

    </div>
  );
};

export { LandingPage };
