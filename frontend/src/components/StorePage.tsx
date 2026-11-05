import { Fragment } from 'react';
import type { ReactNode } from 'react';
import { useExplorerStore } from '../stores/explorerStore';

/** Wraps a Store Explorer page so it remounts, with fresh local state, each
 *  time the explorer store is refreshed. */
const StorePage = ({ children }: { children: ReactNode }) => {
  const version = useExplorerStore((s) => s.version);
  return <Fragment key={version}>{children}</Fragment>;
};

export { StorePage };
