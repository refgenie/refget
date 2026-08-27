import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore';
import { CliCommand } from './CliSnippet';
import type { CodeSnippet } from './CliSnippet';
import { Icon } from './common/Icon';
import type { IconName } from './common/Icon';
import { BaseModal } from './common/BaseModal';
import { cn } from '../utils/cn';

interface StoreNavProps {
  /** Key of the tab to mark current. */
  active?: string;
  /** The `?url=...` query string carried between store pages. */
  storeUrlParam: string;
  /** When set, the code modal also offers the per-collection commands. */
  collectionDigest?: string | null;
}

interface SnippetGroup {
  heading: string;
  snippets: CodeSnippet[];
}

const StoreNav = ({ active, storeUrlParam, collectionDigest }: StoreNavProps) => {
  const [showCode, setShowCode] = useState(false);
  const [codeTab, setCodeTab] = useState<'cli' | 'python'>('cli');
  const { storeUrl } = useExplorerStore();

  const remote = storeUrl || new URLSearchParams(storeUrlParam).get('url') || '';

  const items: Array<{ key: string; label: string; path: string; icon: IconName }> = [
    { key: 'overview', label: 'Overview', path: '/explore-store/overview', icon: 'house' },
    { key: 'sequences', label: 'Sequences', path: '/explore-store/sequences', icon: 'list-ol' },
    { key: 'aliases', label: 'Aliases', path: '/explore-store/aliases', icon: 'tag' },
  ];

  const snippetGroups: SnippetGroup[] = [
    {
      heading: 'Setup',
      snippets: [
        {
          label: 'Subscribe to this remote store',
          cli: `refget config add store \\
  ${remote}`,
          python: `import refget

refget.config.add("store", "${remote}")`,
        },
      ],
    },
    {
      heading: 'Browse',
      snippets: [
        {
          label: 'List collections',
          cli: `refget store list \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.list()`,
        },
        {
          label: 'List sequences',
          cli: `refget store list --sequences \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.list(sequences=True)`,
        },
        {
          label: 'Store statistics',
          cli: `refget store stats \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
print(store)`,
        },
      ],
    },
  ];

  if (collectionDigest) {
    snippetGroups.push({
      heading: 'Collection',
      snippets: [
        {
          label: 'Get collection metadata',
          cli: `refget store get \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.get("${collectionDigest}")`,
        },
        {
          label: 'Pull collection to local cache',
          cli: `refget store pull \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.pull("${collectionDigest}")`,
        },
        {
          label: 'Export as FASTA',
          cli: `refget store export \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.export("${collectionDigest}")`,
        },
        {
          label: 'Generate .fai index',
          cli: `refget store fai \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.fai("${collectionDigest}")`,
        },
        {
          label: 'Generate chrom.sizes',
          cli: `refget store chrom-sizes \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.chrom_sizes("${collectionDigest}")`,
        },
      ],
    });
  }

  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-xl font-light mb-0">
          <Icon name="archive" className="mr-2" />
          RefgetStore Explorer
        </h4>
        <div>
          <button
            className="btn btn--sm btn--outline-secondary mr-2"
            onClick={() => setShowCode(true)}
          >
            <Icon name="code" className="mr-1" />
            Code
          </button>
          <Link to="/explore-store" className="btn btn--sm btn--outline-secondary">
            <Icon name="arrow-left" className="mr-1" />
            Change Store
          </Link>
        </div>
      </div>

      {/* Code Snippets Modal */}
      <BaseModal
        isOpen={showCode}
        onClose={() => setShowCode(false)}
        title="Code Snippets"
        size="lg"
      >
        <ul className="tabs tabs--pills mb-4">
          <li>
            <button
              className={cn('tab', codeTab === 'cli' && 'tab--active')}
              onClick={() => setCodeTab('cli')}
            >
              <Icon name="terminal" className="mr-1" />
              CLI
            </button>
          </li>
          <li>
            <button
              className={cn('tab', codeTab === 'python' && 'tab--active')}
              onClick={() => setCodeTab('python')}
            >
              <Icon name="python" className="mr-1" />
              Python
            </button>
          </li>
        </ul>

        {snippetGroups.map((group, gi) => (
          <div key={gi} className={gi < snippetGroups.length - 1 ? 'mb-6' : ''}>
            <h6 className="text-muted mb-2">{group.heading}</h6>
            {group.snippets.map((snippet, i) => (
              <div key={i} className={i < group.snippets.length - 1 ? 'mb-4' : ''}>
                <small className="text-muted block mb-1 text-sm">{snippet.label}</small>
                <CliCommand command={snippet[codeTab]} />
              </div>
            ))}
          </div>
        ))}
        <hr className="my-4" />
        <small className="text-muted text-sm">
          Install: <code className="code code--inline">pip install refget</code>
        </small>
      </BaseModal>

      <ul className="tabs tabs--bordered mb-4">
        {items.map((item) => (
          <li key={item.key}>
            <Link
              to={`${item.path}${storeUrlParam}`}
              className={cn('tab', active === item.key && 'tab--active')}
            >
              <Icon name={item.icon} className='mr-1' />
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

export { StoreNav };
