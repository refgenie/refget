import { create } from 'zustand'
import type { CollectionListing, CustomCollection, SimilarityRow } from '../types'

type Updater<T> = T | ((current: T) => T)

export interface SimilaritiesState {
  selectedCollectionsIndex: boolean[];
  customCollections: CustomCollection[];
  customCollectionName: string;
  customCollectionJSON: string;
  customCount: number;
  similarities: SimilarityRow[] | null;
  error: string | null;
  sortBy: string | null;
  sortAscending: boolean;
  species: string;
  setSpecies: (value: string) => void;
  setError: (value: string | null) => void;
  resetSort: () => void;
  sortByColumn: (column: string) => void;
  setSelectedCollectionsIndex: (value: Updater<boolean[]>) => void;
  setCustomCollections: (value: Updater<CustomCollection[]>) => void;
  setCustomCollectionName: (value: string) => void;
  setCustomCollectionJSON: (value: string) => void;
  setCustomCount: (value: Updater<number>) => void;
  setSimilarities: (value: SimilarityRow[] | null) => void;
  getAllCollections: (collections: CollectionListing | null | undefined) => string[];
  initializeSelectedCollections: (collections: CollectionListing | null | undefined) => void;
}

/**
 * Order two rows by one attribute. Numeric scores sort numerically, everything
 * else lexically, which is what the matrix headers offer.
 */
const compareBy = (key: string, ascending: boolean, numeric: boolean) =>
  (a: SimilarityRow, b: SimilarityRow) => {
    if (numeric) {
      const va = Number(a[key] ?? 0)
      const vb = Number(b[key] ?? 0)
      return ascending ? va - vb : vb - va
    }
    return ascending
      ? String(a[key]).localeCompare(String(b[key]))
      : String(b[key]).localeCompare(String(a[key]))
  }

export const useSimilaritiesStore = create<SimilaritiesState>()((set, get) => ({
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

    const sampleValue = similarities.find((item) => item[newSortBy] != null)?.[newSortBy];

    const sorted = [...similarities];
    sorted.sort(compareBy(newSortBy, newSortAscending, typeof sampleValue === 'number'));

    set({ sortBy: newSortBy, sortAscending: newSortAscending, similarities: sorted });
  },

  setSelectedCollectionsIndex: (value) => {
    if (typeof value === 'function') {
      const currentValue = get().selectedCollectionsIndex;
      set({ selectedCollectionsIndex: (value as (current: boolean[]) => boolean[])(currentValue) });
    } else {
      set({ selectedCollectionsIndex: value });
    }
  },
  
  setCustomCollections: (value) => {
    if (typeof value === 'function') {
      const currentValue = get().customCollections;
      set({ customCollections: (value as (current: CustomCollection[]) => CustomCollection[])(currentValue) });
    } else {
      set({ customCollections: value });
    }
  },

  setCustomCollectionName: (value) => set({ customCollectionName: value }),
  setCustomCollectionJSON: (value) => set({ customCollectionJSON: value }),
  
  setCustomCount: (value) => {
    if (typeof value === 'function') {
      const currentValue = get().customCount;
      set({ customCount: (value as (current: number) => number)(currentValue) });
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

    const sampleValue = value.find((item) => item[sortBy] != null)?.[sortBy];

    const sorted = [...value];
    sorted.sort(compareBy(sortBy, sortAscending, typeof sampleValue === 'number'));

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
