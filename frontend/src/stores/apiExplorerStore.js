import { create } from 'zustand';
import { fetchServiceInfoFromUrl } from '../services/fetchData.jsx';

const RECENT_APIS_KEY = 'refget-explorer-recent-apis';
const MAX_RECENT = 5;

const getRecentApis = () => {
  try {
    return JSON.parse(localStorage.getItem(RECENT_APIS_KEY)) || [];
  } catch {
    return [];
  }
};

const saveRecentApi = (url) => {
  const recent = getRecentApis().filter((u) => u !== url);
  recent.unshift(url);
  localStorage.setItem(
    RECENT_APIS_KEY,
    JSON.stringify(recent.slice(0, MAX_RECENT)),
  );
};

export const useApiExplorerStore = create((set, get) => ({
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
      set({ serviceInfo: null, apiAvailable: false, loading: false, error: err.message });
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
