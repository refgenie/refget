import { create } from 'zustand';
import { fetchServiceInfoFromUrl } from '../services/fetchData';
import type { ServiceInfo } from '../types';
import { errorMessage } from '../utils/errors';

export interface ApiExplorerState {
  apiUrl: string | null;
  serviceInfo: ServiceInfo | null;
  apiAvailable: boolean;
  loading: boolean;
  error: string | null;
  probeApi: (url: string) => Promise<ServiceInfo>;
  reset: () => void;
  getRecentApis: () => string[];
}

const RECENT_APIS_KEY = 'refget-explorer-recent-apis';
const MAX_RECENT = 5;

const getRecentApis = (): string[] => {
  try {
    return JSON.parse(localStorage.getItem(RECENT_APIS_KEY) ?? 'null') || [];
  } catch {
    return [];
  }
};

const saveRecentApi = (url: string) => {
  const recent = getRecentApis().filter((u: string) => u !== url);
  recent.unshift(url);
  localStorage.setItem(
    RECENT_APIS_KEY,
    JSON.stringify(recent.slice(0, MAX_RECENT)),
  );
};

export const useApiExplorerStore = create<ApiExplorerState>()((set) => ({
  apiUrl: null,
  serviceInfo: null,
  apiAvailable: false,
  loading: false,
  error: null,

  probeApi: async (url) => {
    const trimmed = url.replace(/\/+$/, '');
    set({ loading: true, error: null, apiUrl: trimmed });
    try {
      const info = await fetchServiceInfoFromUrl(trimmed);
      saveRecentApi(trimmed);
      set({ serviceInfo: info, apiAvailable: true, loading: false });
      return info;
    } catch (err) {
      set({
        serviceInfo: null,
        apiAvailable: false,
        loading: false,
        error: err instanceof Error ? errorMessage(err) : String(err),
      });
      throw err;
    }
  },

  reset: () =>
    set({
      apiUrl: null,
      serviceInfo: null,
      apiAvailable: false,
      loading: false,
      error: null,
    }),

  getRecentApis,
}));
