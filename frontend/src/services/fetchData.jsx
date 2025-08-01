import { API_BASE } from '../utilities.jsx';

export const fetchServiceInfo = async () => {
  const response = await fetch(`${API_BASE}/service-info`);
  return response.json();
};

export const fetchPangenomeLevels = async (
  digest,
  level = '2',
  collated = true,
) => {
  const url = `${API_BASE}/pangenome/${digest}?level=1`;
  const url2 = `${API_BASE}/pangenome/${digest}?level=2`;
  const urlItemwise = `${API_BASE}/pangenome/${digest}?collated=false`;
  let resps = [
    fetch(url).then((response) => response.json()),
    fetch(url2).then((response) => response.json()),
    fetch(urlItemwise).then((response) => response.json()),
  ];

  return Promise.all(resps);
};

export const fetchSeqColList = async () => {
  const url = `${API_BASE}/list/collections?page_size=10&page=0`;
  const url2 = `${API_BASE}/list/pangenomes?page_size=5`;
  const url3 = `${API_BASE}/list/attributes/name_length_pairs?page_size=5`;
  let resps = [
    fetch(url).then((response) => response.json()),
    fetch(url2).then((response) => response.json()),
    fetch(url3).then((response) => response.json()),
  ];
  return Promise.all(resps);
};

export const fetchAllSeqCols = async () => {
  const url = `${API_BASE}/list/collections?page_size=1000&page=0`;
  let resps = [fetch(url).then((response) => response.json())];
  return Promise.all(resps);
};

export const fetchSeqColDetails = async (
  digest,
  level = '2',
  collated = true,
) => {
  const url = `${API_BASE}/collection/${digest}?level=${level}&collated=${collated}`;
  return fetch(url).then((response) => response.json());
};

export const fetchCollectionLevels = async (digest) => {
  const urls = [
    `${API_BASE}/collection/${digest}?level=1`,
    `${API_BASE}/collection/${digest}?level=2`,
    `${API_BASE}/collection/${digest}?collated=false`,
  ];

  const responses = await Promise.all(
    urls.map((url) =>
      fetch(url).then((response) => {
        if (!response.ok) {
          throw new Error(
            `Error fetching data from ${url}: ${response.statusText}`,
          );
        }
        return response.json();
      }),
    ),
  );

  return responses;
};

export const fetchComparison = async (digest1, digest2) => {
  const url = `${API_BASE}/comparison/${digest1}/${digest2}`;
  return fetch(url).then((response) => response.json());
};

export const fetchComparisonJSON = async (data, digest) => {
  const url = `${API_BASE}/comparison/${digest}`;
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  }).then((response) => response.json());
};

export const fetchAttribute = async (attribute, digest) => {
  const url = `${API_BASE}/list/collections/${attribute}/${digest}`;
  const url2 = `${API_BASE}/attribute/collection/${attribute}/${digest}`;
  let resps = [
    fetch(url).then((response) => response.json()),
    fetch(url2).then((response) => response.json()),
  ];
  return Promise.all(resps);
};

export const fetchSimilarities = async (digest) => {
  const url = `${API_BASE}/similarities/${digest}?page_size=500`;
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  }).then((response) => response.json());
};

export const fetchSimilaritiesJSON = async (data) => {
  const url = `${API_BASE}/similarities/?page_size=500`;
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  }).then((response) => response.json());
};
