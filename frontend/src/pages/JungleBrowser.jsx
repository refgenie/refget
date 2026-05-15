import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import jungleData from '../data/jungle.json';

const AUTHORITY_COLORS = {
  ncbi: 'primary',
  ucsc: 'success',
  ensembl: 'warning',
  gencode: 'info',
  broad: 'danger',
  ddbj: 'secondary',
  ENA: 'dark',
  igenomes: 'secondary',
  refgenie: 'primary',
  '1000genomes': 'dark',
};

const JungleBrowser = () => {
  const [speciesFilter, setSpeciesFilter] = useState('all');
  const [genomeFilter, setGenomeFilter] = useState('all');
  const [authorityFilter, setAuthorityFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Get unique values for filters
  const species = useMemo(() => [...new Set(jungleData.map(d => d.species))].sort(), []);
  const genomes = useMemo(() => [...new Set(jungleData.map(d => d.genome))].sort(), []);
  const authorities = useMemo(() => [...new Set(jungleData.map(d => d.authority))].sort(), []);

  // Filter data
  const filteredData = useMemo(() => {
    return jungleData.filter(d => {
      if (speciesFilter !== 'all' && d.species !== speciesFilter) return false;
      if (genomeFilter !== 'all' && d.genome !== genomeFilter) return false;
      if (authorityFilter !== 'all' && d.authority !== authorityFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return d.name.toLowerCase().includes(q) ||
               d.description.toLowerCase().includes(q) ||
               d.digest.toLowerCase().includes(q);
      }
      return true;
    });
  }, [speciesFilter, genomeFilter, authorityFilter, searchQuery]);

  // Group by genome for summary
  const genomeCounts = useMemo(() => {
    const counts = {};
    jungleData.forEach(d => {
      counts[d.genome] = (counts[d.genome] || 0) + 1;
    });
    return counts;
  }, []);

  return (
    <div className="mb-5">
      <h3 className="fw-light mb-3">
        <i className="bi bi-tree me-2" />
        The Reference Genome Jungle
      </h3>
      <p className="text-muted">
        A curated collection of {jungleData.length} reference genome assemblies from major providers,
        with provenance tracking and sequence collection digests.
      </p>

      <div className="alert alert-light border mb-4">
        <div className="d-flex align-items-start">
          <i className="bi bi-journal-text me-3 fs-5 text-primary" />
          <div>
            This is the data used for the paper:{' '}
            <a href="https://doi.org/10.1101/2025.10.06.680641" target="_blank" rel="noopener noreferrer">
              Taming the reference genome jungle: the refget sequence collection standard
            </a>
            <span className="text-muted small ms-1">
              (Campbell et al., 2025)
            </span>
          </div>
        </div>
      </div>

      {/* Genome quick links */}
      <div className="mb-4">
        <span className="text-muted small me-2">Jump to:</span>
        {Object.entries(genomeCounts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 8)
          .map(([genome, count]) => (
            <button
              key={genome}
              className={`btn btn-sm me-1 mb-1 ${genomeFilter === genome ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => setGenomeFilter(genomeFilter === genome ? 'all' : genome)}
            >
              {genome} <span className="badge bg-light text-dark">{count}</span>
            </button>
          ))}
      </div>

      {/* Filters */}
      <div className="row g-2 mb-4">
        <div className="col-md-3">
          <input
            type="text"
            className="form-control form-control-sm"
            placeholder="Search name, description, or digest..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="col-md-2">
          <select
            className="form-select form-select-sm"
            value={speciesFilter}
            onChange={(e) => setSpeciesFilter(e.target.value)}
          >
            <option value="all">All species</option>
            {species.map(s => (
              <option key={s} value={s}>{s.replace('_', ' ')}</option>
            ))}
          </select>
        </div>
        <div className="col-md-2">
          <select
            className="form-select form-select-sm"
            value={genomeFilter}
            onChange={(e) => setGenomeFilter(e.target.value)}
          >
            <option value="all">All genomes</option>
            {genomes.map(g => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>
        <div className="col-md-2">
          <select
            className="form-select form-select-sm"
            value={authorityFilter}
            onChange={(e) => setAuthorityFilter(e.target.value)}
          >
            <option value="all">All authorities</option>
            {authorities.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <div className="col-md-3 text-muted small d-flex align-items-center">
          Showing {filteredData.length} of {jungleData.length} references
        </div>
      </div>

      {/* Table */}
      <div className="table-responsive">
        <table className="table table-sm table-hover">
          <thead className="table-light">
            <tr>
              <th>Name</th>
              <th>Genome</th>
              <th>Authority</th>
              <th>Sequences</th>
              <th>Downloaded</th>
              <th>Links</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((ref) => (
              <tr key={ref.name}>
                <td>
                  <div>
                    <strong className="d-block">{ref.name}</strong>
                    <small className="text-muted">{ref.description}</small>
                  </div>
                </td>
                <td>
                  <span className="badge bg-light text-dark">{ref.genome}</span>
                </td>
                <td>
                  <span className={`badge bg-${AUTHORITY_COLORS[ref.authority] || 'secondary'}`}>
                    {ref.authority}
                  </span>
                </td>
                <td className="text-end">{ref.sequenceCount.toLocaleString()}</td>
                <td className="small text-muted">{ref.downloadDate}</td>
                <td>
                  <div className="btn-group btn-group-sm">
                    <Link
                      to={`/collection/${ref.digest}`}
                      className="btn btn-outline-primary btn-sm"
                      title="View collection details"
                    >
                      <i className="bi bi-eye" />
                    </Link>
                    <Link
                      to={`/scom?digest=${ref.digest}&name=${encodeURIComponent(ref.name)}`}
                      className="btn btn-outline-secondary btn-sm"
                      title="Compare with SCOM"
                    >
                      <i className="bi bi-arrow-left-right" />
                    </Link>
                    {ref.sourceUrl && (
                      <a
                        href={ref.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-outline-dark btn-sm"
                        title="Download original file"
                      >
                        <i className="bi bi-download" />
                      </a>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredData.length === 0 && (
        <div className="text-center text-muted py-5">
          No references match your filters.
        </div>
      )}
    </div>
  );
};

export { JungleBrowser };
