import { create } from 'zustand'

export const useSimilaritiesStore = create((set, get) => ({
  selectedCollectionsIndex: [],
  customCollections: [],
  customCollectionName: '',
  customCollectionJSON: '',
  customCount: 1,
  similarities: null,

  setSelectedCollectionsIndex: (value) => {
    if (typeof value === 'function') {
      const currentValue = get().selectedCollectionsIndex;
      set({ selectedCollectionsIndex: value(currentValue) });
    } else {
      set({ selectedCollectionsIndex: value });
    }
  },
  
  setCustomCollections: (value) => {
    if (typeof value === 'function') {
      const currentValue = get().customCollections;
      set({ customCollections: value(currentValue) });
    } else {
      set({ customCollections: value });
    }
  },

  setCustomCollectionName: (value) => set({ customCollectionName: value }),
  setCustomCollectionJSON: (value) => set({ customCollectionJSON: value }),
  
  setCustomCount: (value) => {
    if (typeof value === 'function') {
      const currentValue = get().customCount;
      set({ customCount: value(currentValue) });
    } else {
      set({ customCount: value });
    }
  },

  setSimilarities: (value) => set({ similarities: value }),

  getAllCollections: (collections) => {
    const { customCollections } = get();
    return [
      ...(collections?.results || []),
      ...customCollections.map((c) => c.selectedDigest),
    ];
  },

  initializeSelectedCollections: (collections) => {
    const current = get().selectedCollectionsIndex;
    if (current.length === 0 && collections?.results) {
      set({ selectedCollectionsIndex: collections.results.map(() => false) });
    }
  },
}));
