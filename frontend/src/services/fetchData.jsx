import { API_BASE } from '../utilities.jsx';

export class AppError extends Error {
  constructor(message, { status, isNotFound, digest1, digest2 } = {}) {
    super(message);
    this.name = 'AppError';
    this.status = status ?? null;
    this.isNotFound = isNotFound ?? false;
    this.digest1 = digest1 ?? null;
    this.digest2 = digest2 ?? null;
  }
}

const checkResponse = async (response, url) => {
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

export const fetchServiceInfo = async () => {
  const url = `${API_BASE}/service-info`;
  const response = await fetch(url);
  await checkResponse(response, url);
  return response.json();
};

export const fetchPangenomeLevels = async (digest) => {
  const urls = [
    `${API_BASE}/pangenome/${digest}?level=1`,
    `${API_BASE}/pangenome/${digest}?level=2`,
    `${API_BASE}/pangenome/${digest}?collated=false`,
  ];

  return Promise.all(
    urls.map(async (url) => {
      const response = await fetch(url);
      await checkResponse(response, url);
      return response.json();
    }),
  );
};

export const fetchSeqColList = async () => {
  const urls = [
    `${API_BASE}/list/collection?page_size=10&page=0`,
    `${API_BASE}/list/pangenome?page_size=5`,
    `${API_BASE}/list/attributes/name_length_pairs?page_size=5`,
  ];

  return Promise.all(
    urls.map(async (url) => {
      const response = await fetch(url);
      await checkResponse(response, url);
      return response.json();
    }),
  );
};

export const fetchAllSeqCols = async () => {
  const urls = [
    `${API_BASE}/list/collection?page_size=1000&page=0`,
  ];

  return Promise.all(
    urls.map(async (url) => {
      const response = await fetch(url);
      await checkResponse(response, url);
      return response.json();
    }),
  );
};

export const fetchCollectionLevels = async (digest) => {
  const urls = [
    `${API_BASE}/collection/${digest}?level=1`,
    `${API_BASE}/collection/${digest}?level=2`,
    `${API_BASE}/collection/${digest}?collated=false`,
  ];

  return Promise.all(
    urls.map(async (url) => {
      const response = await fetch(url);
      await checkResponse(response, url);
      return response.json();
    }),
  );
};

export const fetchComparison = async (digest1, digest2) => {
  const url = `${API_BASE}/comparison/${digest1}/${digest2}`;
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

export const fetchComparisonJSON = async (data, digest) => {
  const url = `${API_BASE}/comparison/${digest}`;
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

export const fetchAttribute = async (attribute, digest) => {
  const urls = [
    `${API_BASE}/list/collection?${attribute}=${digest}`,
    `${API_BASE}/attribute/collection/${attribute}/${digest}`,
  ];

  return Promise.all(
    urls.map(async (url) => {
      const response = await fetch(url);
      await checkResponse(response, url);
      return response.json();
    }),
  );
};

export const fetchSimilarities = async (digest) => {
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

export const fetchSimilaritiesJSON = async (data, species) => {
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
