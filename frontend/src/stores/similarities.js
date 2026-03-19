import { create } from 'zustand'

export const useSimilaritiesStore = create((set, get) => ({
  selectedCollectionsIndex: [],
  customCollections: [],
  customCollectionName: '',
  customCollectionJSON: '',
  customCount: 1,
  similarities: null,
  error: null,
  sortBy: null,
  sortAscending: false,
  species: 'human',

  setSpecies: (value) => set({ species: value }),
  setError: (value) => set({ error: value }),

  resetSort: () => set({ sortBy: null, sortAscending: false }),

  sortByColumn: (column) => {
    const { similarities, sortBy, sortAscending } = get();

    const newSortBy = column;
    const newSortAscending = sortBy === column ? !sortAscending : false;

    if (!similarities) {
      set({ sortBy: newSortBy, sortAscending: newSortAscending });
      return;
    }

    const sampleValue = similarities.find(item => item[newSortBy] != null)?.[newSortBy];

    const sorted = [...similarities];

    if (typeof sampleValue === 'number') {
      sorted.sort((a, b) => newSortAscending ? a[newSortBy] - b[newSortBy] : b[newSortBy] - a[newSortBy]);
    } else {
      sorted.sort((a, b) => newSortAscending
        ? String(a[newSortBy]).localeCompare(String(b[newSortBy]))
        : String(b[newSortBy]).localeCompare(String(a[newSortBy]))
      );
    }

    set({ sortBy: newSortBy, sortAscending: newSortAscending, similarities: sorted });
  },

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

  setSimilarities: (value) => {
    const { sortBy, sortAscending } = get();

    if (!sortBy || !value) {
      set({ similarities: value });
      return;
    }

    const sampleValue = value.find(item => item[sortBy] != null)?.[sortBy];

    const sorted = [...value];

    if (typeof sampleValue === 'number') {
      sorted.sort((a, b) => sortAscending ? a[sortBy] - b[sortBy] : b[sortBy] - a[sortBy]);
    } else {
      sorted.sort((a, b) => sortAscending
        ? String(a[sortBy]).localeCompare(String(b[sortBy]))
        : String(b[sortBy]).localeCompare(String(a[sortBy]))
      );
    }

    set({ similarities: sorted });
  },

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
