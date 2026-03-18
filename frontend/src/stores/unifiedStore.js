import { create } from 'zustand';
import { API_BASE } from '../utilities.jsx';
import { fetchStoreMetadata, fetchCollectionIndex } from '../services/storeService.js';

export const useUnifiedStore = create((set, get) => ({
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
    let storeUrl = null;
    let storeMetadata = null;
    let storeCollections = null;
    let serviceInfo = null;

    // First, fetch /service-info to discover the API and store URL
    try {
      const resp = await fetch(`${API_BASE}/service-info`);
      if (resp.ok) {
        hasAPI = true;
        serviceInfo = await resp.json();

        // Extract store URL from service-info
        const storeConfig = serviceInfo?.seqcol?.refget_store;
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
