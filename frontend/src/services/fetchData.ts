import { API_BASE } from '../utilities';
import type {
  ComparisonResult,
  SeqColLevel1,
  SeqColLevel2,
  ServiceInfo,
} from '../types';

interface AppErrorOptions {
  status?: number | null;
  isNotFound?: boolean;
  digest1?: string | null;
  digest2?: string | null;
}

export class AppError extends Error {
  status: number | null;
  isNotFound: boolean;
  digest1: string | null;
  digest2: string | null;

  constructor(message: string, { status, isNotFound, digest1, digest2 }: AppErrorOptions = {}) {
    super(message);
    this.name = 'AppError';
    this.status = status ?? null;
    this.isNotFound = isNotFound ?? false;
    this.digest1 = digest1 ?? null;
    this.digest2 = digest2 ?? null;
  }
}

const checkResponse = async (response: Response, url: string): Promise<Response> => {
  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorData.message || errorData.error || errorDetail;
    } catch {
      try {
        errorDetail = await response.text();
        if (errorDetail.length > 200) {
          errorDetail = errorDetail.substring(0, 200) + '...';
        }
      } catch {
        // Fallback to status text if body cannot be read
      }
    }
    throw new Error(`HTTP ${response.status} from ${url}: ${errorDetail}`);
  }
  return response;
};

export const fetchServiceInfo = async (): Promise<ServiceInfo | null> => {
  try {
    const url = `${API_BASE}/service-info`;
    const response = await fetch(url);
    await checkResponse(response, url);
    return response.json();
  } catch {
    return null;
  }
};

export const fetchServiceInfoFromUrl = async (baseUrl: string): Promise<ServiceInfo> => {
  const url = `${baseUrl.replace(/\/+$/, '')}/service-info`;
  const response = await fetch(url);
  await checkResponse(response, url);
  return response.json();
};

export const fetchPangenomeLevels = async (digest: string) => {
  const urls = [
    `${API_BASE}/pangenome/${digest}?level=1`,
    `${API_BASE}/pangenome/${digest}?level=2`,
    `${API_BASE}/pangenome/${digest}?collated=false`,
  ];

  return Promise.all(
    urls.map(async (url: string) => {
      const response = await fetch(url);
      await checkResponse(response, url);
      return response.json();
    }),
  );
};

export const fetchSeqColList = async (baseUrl: string | null, opts: RequestInit = {}) => {
  const base = (baseUrl || API_BASE).replace(/\/+$/, '');
  const fetchRequired = async (url: string) => {
    const response = await fetch(url, opts);
    await checkResponse(response, url);
    return response.json();
  };

  const fetchOptional = async (url: string) => {
    try {
      const response = await fetch(url, opts);
      if (!response.ok) return null;
      return response.json();
    } catch {
      return null;
    }
  };

  return Promise.all([
    fetchRequired(`${base}/list/collection?page_size=10&page=0`),
    fetchOptional(`${base}/list/pangenome?page_size=5`),
    fetchRequired(`${base}/list/attributes/name_length_pairs?page_size=5`),
  ]);
};

export const fetchAllSeqCols = async (baseUrl?: string | null) => {
  const base = (baseUrl || API_BASE).replace(/\/+$/, '');
  const urls = [
    `${base}/list/collection?page_size=1000&page=0`,
  ];

  return Promise.all(
    urls.map(async (url: string) => {
      const response = await fetch(url);
      await checkResponse(response, url);
      return response.json();
    }),
  );
};

export const fetchCollectionLevels = async (
  digest: string,
  baseUrl?: string | null,
): Promise<[SeqColLevel1, SeqColLevel2, SeqColLevel2]> => {
  const base = (baseUrl || API_BASE).replace(/\/+$/, '');
  const urls = [
    `${base}/collection/${digest}?level=1`,
    `${base}/collection/${digest}?level=2`,
    `${base}/collection/${digest}?collated=false`,
  ];

  return Promise.all(
    urls.map(async (url: string) => {
      const response = await fetch(url);
      await checkResponse(response, url);
      return response.json();
    }),
  ) as Promise<[SeqColLevel1, SeqColLevel2, SeqColLevel2]>;
};

export const fetchComparison = async (
  digest1: string,
  digest2: string,
  baseUrl?: string | null,
): Promise<ComparisonResult> => {
  const base = (baseUrl || API_BASE).replace(/\/+$/, '');
  const url = `${base}/comparison/${digest1}/${digest2}`;
  const response = await fetch(url);
  if (!response.ok) {
    if (response.status === 404) {
      throw new AppError('Collection not found', {
        status: 404,
        isNotFound: true,
        digest1,
        digest2,
      });
    }
    await checkResponse(response, url);
  }
  return response.json();
};

export const fetchComparisonJSON = async (
  data: unknown,
  digest: string,
  baseUrl?: string | null,
): Promise<ComparisonResult> => {
  const base = (baseUrl || API_BASE).replace(/\/+$/, '');
  const url = `${base}/comparison/${digest}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  await checkResponse(response, url);
  return response.json();
};

export const fetchAttribute = async (
  attribute: string,
  digest: string,
  baseUrl?: string | null,
) => {
  const base = (baseUrl || API_BASE).replace(/\/+$/, '');
  const urls = [
    `${base}/list/collection?${attribute}=${digest}`,
    `${base}/attribute/collection/${attribute}/${digest}`,
  ];

  return Promise.all(
    urls.map(async (url: string) => {
      const response = await fetch(url);
      await checkResponse(response, url);
      return response.json();
    }),
  );
};

export const fetchSimilarities = async (digest: string) => {
  const url = `${API_BASE}/similarities/${digest}?page_size=60`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  await checkResponse(response, url);
  return response.json();
};

export const fetchSimilaritiesJSON = async (data: unknown, species: string) => {
  const url = `${API_BASE}/similarities/?species=${species}&page_size=60`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  await checkResponse(response, url);
  return response.json();
};
