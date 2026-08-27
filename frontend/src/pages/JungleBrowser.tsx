import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import jungleData from '../data/jungle.json';
import { Icon } from '../components/common/Icon';

/** Badge modifier per source authority, so a provider keeps one colour. */
const AUTHORITY_COLORS: Record<string, string> = {
  ncbi: 'badge--primary',
  ucsc: 'badge--success',
  ensembl: 'badge--warning',
  gencode: 'badge--info',
  broad: 'badge--danger',
  ddbj: 'badge--secondary',
  ENA: 'badge--secondary',
  igenomes: 'badge--secondary',
  refgenie: 'badge--primary',
  '1000genomes': 'badge--secondary',
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
    const counts: Record<string, number> = {};
    jungleData.forEach((d) => {
      counts[d.genome] = (counts[d.genome] || 0) + 1;
    });
    return counts;
  }, []);

  return (
    <div className="mb-12">
      <h3 className="font-light mb-4">
        <Icon name="tree" className="mr-2" />
        The Reference Genome Jungle
      </h3>
      <p className="text-muted">
        A curated collection of {jungleData.length} reference genome assemblies from major providers,
        with provenance tracking and sequence collection digests.
      </p>

      <div className="alert alert--muted border mb-6">
        <div className="flex items-start">
          <Icon name="journal" className="mr-4 text-lg text-primary-fg" />
          <div>
            This is the data used for the paper:{' '}
            <a href="https://doi.org/10.1101/2025.10.06.680641" target="_blank" rel="noopener noreferrer">
              Taming the reference genome jungle: the refget sequence collection standard
            </a>
            <span className="text-muted text-sm ml-1">
              (Campbell et al., 2025)
            </span>
          </div>
        </div>
      </div>

      {/* Genome quick links */}
      <div className="mb-6">
        <span className="text-muted text-sm mr-2">Jump to:</span>
        {Object.entries(genomeCounts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 8)
          .map(([genome, count]) => (
            <button
              key={genome}
              className={`btn btn--sm mr-1 mb-1 ${genomeFilter === genome ? 'btn--primary' : 'btn--outline-secondary'}`}
              onClick={() => setGenomeFilter(genomeFilter === genome ? 'all' : genome)}
            >
              {genome} <span className="badge bg-surface-muted text-strong">{count}</span>
            </button>
          ))}
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2 mb-6">
        <div>
          <input
            type="text"
            className="form-input form-input--sm"
            placeholder="Search name, description, or digest..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div>
          <select
            className="form-select form-select--sm"
            value={speciesFilter}
            onChange={(e) => setSpeciesFilter(e.target.value)}
          >
            <option value="all">All species</option>
            {species.map(s => (
              <option key={s} value={s}>{s.replace('_', ' ')}</option>
            ))}
          </select>
        </div>
        <div>
          <select
            className="form-select form-select--sm"
            value={genomeFilter}
            onChange={(e) => setGenomeFilter(e.target.value)}
          >
            <option value="all">All genomes</option>
            {genomes.map(g => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>
        <div>
          <select
            className="form-select form-select--sm"
            value={authorityFilter}
            onChange={(e) => setAuthorityFilter(e.target.value)}
          >
            <option value="all">All authorities</option>
            {authorities.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <div className="text-muted text-sm flex items-center">
          Showing {filteredData.length} of {jungleData.length} references
        </div>
      </div>

      {/* Table */}
      <div className="table-wrap">
        <table className="table table--sm table--hover">
          <thead className="">
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
                    <strong className="block">{ref.name}</strong>
                    <small className="text-muted">{ref.description}</small>
                  </div>
                </td>
                <td>
                  <span className="badge bg-surface-muted text-strong">{ref.genome}</span>
                </td>
                <td>
                  <span className={`badge ${AUTHORITY_COLORS[ref.authority] || 'badge--secondary'}`}>
                    {ref.authority}
                  </span>
                </td>
                <td className="text-right">{ref.sequenceCount.toLocaleString()}</td>
                <td className="text-sm text-muted">{ref.downloadDate}</td>
                <td>
                  <div className="btn-group">
                    <Link
                      to={`/collection/${ref.digest}`}
                      className="btn btn--outline-primary btn--sm"
                      title="View collection details"
                    >
                      <Icon name="eye" />
                    </Link>
                    <Link
                      to={`/scom?digest=${ref.digest}&name=${encodeURIComponent(ref.name)}`}
                      className="btn btn--outline-secondary btn--sm"
                      title="Compare with SCOM"
                    >
                      <Icon name="arrow-left-right" />
                    </Link>
                    {ref.sourceUrl && (
                      <a
                        href={ref.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn--outline-secondary btn--sm"
                        title="Download original file"
                      >
                        <Icon name="download" />
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
        <div className="text-center text-muted py-12">
          No references match your filters.
        </div>
      )}
    </div>
  );
};

export { JungleBrowser };
