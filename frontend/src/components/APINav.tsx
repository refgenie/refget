import { Link } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore';
import { Icon } from './common/Icon';
import type { IconName } from './common/Icon';
import { cn } from '../utils/cn';

interface APINavProps {
  /** Key of the tab to mark current. */
  active?: string;
}

interface NavTab {
  key: string;
  label: string;
  path: string;
  icon: IconName;
}

const APINav = ({ active }: APINavProps) => {
  const { apiUrl } = useApiExplorerStore();
  const urlParam = apiUrl ? `?url=${encodeURIComponent(apiUrl)}` : '';

  const items: NavTab[] = [
    { key: 'collections', label: 'Collections', path: '/explore-api/collections', icon: 'collection' },
    { key: 'compare', label: 'Compare (SCIM)', path: '/explore-api/compare', icon: 'collapse' },
  ];

  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-xl font-light mb-0">
          <Icon name="cloud" className="mr-2" />
          API Explorer
        </h4>
        <Link to="/explore-api" className="btn btn--sm btn--outline-secondary">
          <Icon name="arrow-left" className="mr-1" />
          Change API
        </Link>
      </div>

      {apiUrl && (
        <div className="text-muted text-sm mb-2">
          <Icon name="link" className="mr-1" />
          {apiUrl}
        </div>
      )}

      <ul className="tabs tabs--bordered mb-4">
        {items.map((item) => (
          <li key={item.key}>
            <Link
              to={`${item.path}${urlParam}`}
              className={cn('tab', active === item.key && 'tab--active')}
            >
              <Icon name={item.icon} className="mr-1" />
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

export { APINav };
