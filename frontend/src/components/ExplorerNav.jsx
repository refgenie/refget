import { Link } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore.js';

const ExplorerNav = ({ active }) => {
  const { hasStore, hasAPI } = useUnifiedStore();

  const items = [
    { key: 'collections', label: 'Collections', path: '/collections', icon: 'bi-collection' },
    { key: 'sequences', label: 'Sequences', path: '/sequences', icon: 'bi-list-ol', requireStore: true },
    { key: 'aliases', label: 'Aliases', path: '/aliases', icon: 'bi-tag', requireStore: true },
    { key: 'compare', label: 'Compare', path: '/compare', icon: 'bi-arrows-angle-contract', requireAPI: true },
  ];

  const visibleItems = items.filter((item) => {
    if (item.requireStore && !hasStore) return false;
    if (item.requireAPI && !hasAPI) return false;
    return true;
  });

  return (
    <ul className="nav nav-tabs mb-4">
      {visibleItems.map((item) => (
        <li className="nav-item" key={item.key}>
          <Link
            to={item.path}
            className={`nav-link ${active === item.key ? 'active' : ''}`}
          >
            <i className={`bi ${item.icon} me-1`} />
            {item.label}
          </Link>
        </li>
      ))}
    </ul>
  );
};

export { ExplorerNav };
