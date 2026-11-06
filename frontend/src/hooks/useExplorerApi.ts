import { createContext, useContext } from 'react';

/**
 * The SeqCol API the API Explorer is browsing, for components (digest links,
 * comparison views) that are shared with this site's own pages. Explorer
 * pages provide it; everywhere else it is null and those components link to
 * this site's own pages, which use API_BASE.
 */
export const ExplorerApiContext = createContext<string | null>(null);

export const useExplorerApi = (): string | null => useContext(ExplorerApiContext);
