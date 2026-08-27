import { Link } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore';
import { Icon } from './common/Icon';
import type { IconName } from './common/Icon';
import { cn } from '../utils/cn';

interface ExplorerNavProps {
  /** Key of the tab to mark current. */
  active?: string;
}

interface NavTab {
  key: string;
  label: string;
  path: string;
  icon: IconName;
  requireStore?: boolean;
  requireAPI?: boolean;
}

const ExplorerNav = ({ active }: ExplorerNavProps) => {
  const { hasStore, hasAPI } = useUnifiedStore();

  const items: NavTab[] = [
    { key: 'collections', label: 'Collections', path: '/collections', icon: 'collection' },
    { key: 'sequences', label: 'Sequences', path: '/sequences', icon: 'list-ol', requireStore: true },
    { key: 'aliases', label: 'Aliases', path: '/aliases', icon: 'tag', requireStore: true },
    { key: 'compare', label: 'Compare', path: '/compare', icon: 'collapse', requireAPI: true },
  ];

  const visibleItems = items.filter((item) => {
    if (item.requireStore && !hasStore) return false;
    if (item.requireAPI && !hasAPI) return false;
    return true;
  });

  return (
    <ul className="tabs tabs--bordered mb-6">
      {visibleItems.map((item) => (
        <li key={item.key}>
          <Link
            to={item.path}
            className={cn('tab', active === item.key && 'tab--active')}
          >
            <Icon name={item.icon} className="mr-1" />
            {item.label}
          </Link>
        </li>
      ))}
    </ul>
  );
};

export { ExplorerNav };
