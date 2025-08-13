import { create } from 'zustand'

export const useSimilaritiesStore = create((set, get) => ({
  selectedCollectionsIndex: [],
  customCollections: [],
  customCollectionName: '',
  customCollectionJSON: '',
  customCount: 1,
  similarities: null,
  sortBy: null,
  sortAscending: false,
  species: 'human',

  setSortBy: (value) => set({ sortBy: value }),
  setSortAscending: (value) => set({ sortAscending: value }),
  setSpecies: (value) => set({ species: value }),

  sortSimilarities: () => {
    const { similarities, sortBy, sortAscending } = get();
    
    if (!similarities || !sortBy) return;
    
    const sampleValue = similarities.find(item => item[sortBy] != null)?.[sortBy];
    
    const sorted = [...similarities];
    
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
    
    if (!sortBy) {
      set({ similarities: value });
      return;
    }

    const sampleValue = value.find(item => item[sortBy] != null)?.[sortBy];

    if (typeof sampleValue === 'number') {
      set({ similarities: sortAscending
        ? value.sort((a, b) => a[sortBy] - b[sortBy]) 
        : value.sort((a, b) => b[sortBy] - a[sortBy]) 
      });
    } else {
      set({ similarities: sortAscending
        ? value.sort((a, b) => a[sortBy].localeCompare(b[sortBy])) 
        : value.sort((a, b) => b[sortBy].localeCompare(a[sortBy])) 
      });
    }
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
