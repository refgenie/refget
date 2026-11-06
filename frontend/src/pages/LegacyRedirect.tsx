import { Navigate, useOutletContext, useParams } from 'react-router-dom';
import { API_BASE } from '../utilities';
import storeList from '../data/stores.json';
import type { ServiceInfo } from '../types';

/**
 * The old explorer routes (/collections, /collection/:digest, /sequences,
 * /aliases) browsed this site's own API and the store behind it. They now
 * forward to the Store Explorer for that store, so existing links keep
 * working. Without a known store, they fall back to the API Explorer.
 */
type LegacyPage = 'collections' | 'collection' | 'sequences' | 'aliases';

/** The store behind API_BASE: its stores.json entry, else what the API reports. */
const storeBehindApi = (serviceInfo: ServiceInfo | null | undefined): string | null => {
  const listed = storeList.find((s) => 'api' in s && s.api === API_BASE);
  if (listed) return listed.url;
  const reported = (serviceInfo?.seqcol as { refget_store?: { enabled?: boolean; url?: string } } | undefined)
    ?.refget_store;
  return reported?.enabled && reported.url && /^https?:\/\//i.test(reported.url)
    ? reported.url
    : null;
};

const LegacyRedirect = ({ page }: { page: LegacyPage }) => {
  const { digest } = useParams();
  const { serviceInfo } = useOutletContext<{ serviceInfo: ServiceInfo | null }>() ?? {};
  const store = storeBehindApi(serviceInfo);
  const storeParam = store ? `?url=${encodeURIComponent(store)}` : '';
  const apiParam = `?url=${encodeURIComponent(API_BASE)}`;

  const target = {
    collections: store ? `/explore-store/overview${storeParam}` : `/explore-api/collections${apiParam}`,
    collection: store
      ? `/explore-store/collection/${digest}${storeParam}`
      : `/explore-api/collection/${digest}${apiParam}`,
    sequences: store ? `/explore-store/sequences${storeParam}` : '/explore',
    aliases: store ? `/explore-store/aliases${storeParam}` : '/explore',
  }[page];

  return <Navigate to={target} replace />;
};

export { LegacyRedirect };
