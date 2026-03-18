import { Link } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore.js';

const APINav = ({ active }) => {
  const { apiUrl } = useApiExplorerStore();
  const urlParam = apiUrl ? `?url=${encodeURIComponent(apiUrl)}` : '';

  const items = [
    { key: 'collections', label: 'Collections', path: '/explore-api/collections', icon: 'bi-collection' },
    { key: 'compare', label: 'Compare (SCIM)', path: '/explore-api/compare', icon: 'bi-arrows-angle-contract' },
  ];

  return (
    <div className="mb-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4 className="fw-light mb-0">
          <i className="bi bi-cloud me-2" />
          API Explorer
        </h4>
        <Link to="/explore-api" className="btn btn-sm btn-outline-secondary">
          <i className="bi bi-arrow-left me-1" />
          Change API
        </Link>
      </div>

      {apiUrl && (
        <div className="text-muted small mb-2">
          <i className="bi bi-link-45deg me-1" />
          {apiUrl}
        </div>
      )}

      <ul className="nav nav-tabs mb-3">
        {items.map((item) => (
          <li className="nav-item" key={item.key}>
            <Link
              to={`${item.path}${urlParam}`}
              className={`nav-link ${active === item.key ? 'active' : ''}`}
            >
              <i className={`bi ${item.icon} me-1`} />
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

export { APINav };
