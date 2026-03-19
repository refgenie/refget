import { create } from 'zustand';
import {
  fetchStoreMetadata,
  fetchSequenceIndex,
  fetchCollectionIndex,
  fetchCollection,
  fetchAliases,
  fetchFhrMetadata,
} from '../services/storeService.js';

export const useExplorerStore = create((set, get) => ({
  storeUrl: null,
  metadata: null,
  sequenceIndex: null,       // array of sequence rows (or null if not loaded)
  sequenceIndexPartial: false, // true if only a prefix was loaded
  sequenceIndexTotalSize: 0,   // total file size in bytes
  collections: null,
  loadedCollections: {},
  aliases: {},
  fhrMetadata: {},
  loading: false,
  error: null,

  setStoreUrl: (url) => set({ storeUrl: url }),

  /** Fetch store metadata + collection index (sequence index is lazy-loaded) */
  loadStore: async (url) => {
    set({ loading: true, error: null, storeUrl: url });
    try {
      const metadata = await fetchStoreMetadata(url);
      set({ metadata });

      const collections = await fetchCollectionIndex(url).catch(() => null);

      set({
        sequenceIndex: null,
        sequenceIndexPartial: false,
        sequenceIndexTotalSize: 0,
        collections,
        loading: false,
        loadedCollections: {},
        aliases: {},
        fhrMetadata: {},
      });
    } catch (err) {
      set({ loading: false, error: err.message });
      throw err;
    }
  },

  /** Fetch and cache the sequence index (lazy — only when needed).
   *  Options: { maxBytes } to limit partial load size. */
  loadSequenceIndex: async (options) => {
    const { storeUrl, sequenceIndex } = get();
    // If already fully loaded, return cached
    if (sequenceIndex && !get().sequenceIndexPartial) return sequenceIndex;

    const { rows, partial, totalSize } = await fetchSequenceIndex(storeUrl, options);
    set({
      sequenceIndex: rows,
      sequenceIndexPartial: partial,
      sequenceIndexTotalSize: totalSize,
    });
    return rows;
  },

  /** Fetch and cache a single collection */
  loadCollection: async (digest) => {
    const { storeUrl, loadedCollections } = get();
    if (loadedCollections[digest]) return loadedCollections[digest];

    const data = await fetchCollection(storeUrl, digest);
    set({ loadedCollections: { ...get().loadedCollections, [digest]: data } });
    return data;
  },

  /** Fetch and cache aliases for a type/namespace */
  loadAliases: async (type, namespace) => {
    const { storeUrl, aliases } = get();
    const key = `${type}/${namespace}`;
    if (aliases[key]) return aliases[key];

    const data = await fetchAliases(storeUrl, type, namespace);
    set({ aliases: { ...get().aliases, [key]: data } });
    return data;
  },

  /** Fetch and cache FHR metadata for a collection */
  loadFhrMetadata: async (digest) => {
    const { storeUrl, fhrMetadata } = get();
    if (fhrMetadata[digest] !== undefined) return fhrMetadata[digest];

    const data = await fetchFhrMetadata(storeUrl, digest);
    set({ fhrMetadata: { ...get().fhrMetadata, [digest]: data } });
    return data;
  },

  /** Reset store state */
  reset: () =>
    set({
      storeUrl: null,
      metadata: null,
      sequenceIndex: null,
      sequenceIndexPartial: false,
      sequenceIndexTotalSize: 0,
      collections: null,
      loadedCollections: {},
      aliases: {},
      fhrMetadata: {},
      loading: false,
      error: null,
    }),
}));
