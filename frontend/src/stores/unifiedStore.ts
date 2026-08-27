import { create } from 'zustand';
import { API_BASE } from '../utilities';
import { fetchStoreMetadata, fetchCollectionIndex } from '../services/storeService';
import type { CollectionSummary, ServiceInfo, StoreMetadata } from '../types';

/** service-info's optional pointer at a companion RefgetStore. */
interface StoreConfig {
  enabled?: boolean;
  url?: string;
}

export interface UnifiedState {
  hasStore: boolean;
  hasAPI: boolean;
  storeUrl: string | null;
  apiUrl: string;
  storeMetadata: StoreMetadata | null;
  storeCollections: CollectionSummary[] | null;
  serviceInfo: ServiceInfo | null;
  probed: boolean;
  loading: boolean;
  probe: () => Promise<void>;
}

export const useUnifiedStore = create<UnifiedState>()((set, get) => ({
  hasStore: false,
  hasAPI: false,
  storeUrl: null,
  apiUrl: API_BASE,
  storeMetadata: null,
  storeCollections: null,
  serviceInfo: null,
  probed: false,
  loading: false,

  probe: async () => {
    if (get().probed) return;
    set({ loading: true });

    let hasAPI = false;
    let hasStore = false;
    let storeUrl: string | null = null;
    let storeMetadata: StoreMetadata | null = null;
    let storeCollections: CollectionSummary[] | null = null;
    let serviceInfo: ServiceInfo | null = null;

    // First, fetch /service-info to discover the API and store URL
    try {
      const resp = await fetch(`${API_BASE}/service-info`);
      if (resp.ok) {
        hasAPI = true;
        serviceInfo = await resp.json();

        // Extract store URL from service-info
        const storeConfig = (serviceInfo?.seqcol as { refget_store?: StoreConfig } | undefined)
          ?.refget_store;
        if (storeConfig?.enabled && storeConfig?.url) {
          const candidateUrl = storeConfig.url;

          // Only probe if it's an HTTP(S) URL (browser can't fetch local paths)
          if (/^https?:\/\//i.test(candidateUrl)) {
            try {
              storeMetadata = await fetchStoreMetadata(candidateUrl);
              hasStore = true;
              storeUrl = candidateUrl;
              storeCollections = await fetchCollectionIndex(candidateUrl).catch(() => null);
            } catch {
              hasStore = false;
            }
          }
        }
      }
    } catch {
      hasAPI = false;
    }

    set({
      hasStore,
      hasAPI,
      storeUrl,
      storeMetadata,
      storeCollections,
      serviceInfo,
      probed: true,
      loading: false,
    });
  },
}));
