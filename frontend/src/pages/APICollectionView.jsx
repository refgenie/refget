import { useState, useEffect } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore.js';
import { APINav } from '../components/APINav.jsx';
import { fetchCollectionLevels } from '../services/fetchData.jsx';
import {
  AttributeValue,
  LinkedAttributeDigest,
} from '../components/ValuesAndDigests.jsx';

const APICollectionView = () => {
  const { digest } = useParams();
  const [searchParams] = useSearchParams();
  const { apiUrl, probeApi } = useApiExplorerStore();
  const [collection, setCollection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const urlParam = searchParams.get('url');
  const effectiveUrl = apiUrl || urlParam;

  useEffect(() => {
    const init = async () => {
      try {
        if (urlParam && !apiUrl) {
          await probeApi(urlParam);
        }
        const result = await fetchCollectionLevels(digest, effectiveUrl);
        setCollection(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [digest, urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div>
        <APINav active="collections" />
        <div className="text-center py-5">
          <div className="spinner-border" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <APINav active="collections" />
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  }

  if (!Array.isArray(collection) || collection.length < 3) {
    return (
      <div>
        <APINav active="collections" />
        <div className="alert alert-warning">Failed to load collection data.</div>
      </div>
    );
  }

  const level1 = collection[0];
  const level2 = collection[1];
  const uncollated = collection[2];
  const base = effectiveUrl?.replace(/\/+$/, '') || '';

  const attributeViews = Object.keys(level2).map((attribute) => (
    <div key={attribute}>
      <h6 className="mb-2 mt-4 fw-medium">{attribute}</h6>
      <div className="row align-items-center home">
        <div className="col-md-1 text-muted">Digest:</div>
        <div className="col">
          <LinkedAttributeDigest attribute={attribute} digest={level1[attribute]} />
        </div>
      </div>
      <div className="row align-items-center">
        <div className="col-md-1 text-muted">Value:</div>
        <div className="col">
          <AttributeValue value={level2[attribute]} />
        </div>
      </div>
    </div>
  ));

  return (
    <div>
      <APINav active="collections" />

      <h4 className="fw-light">Sequence Collection: {digest}</h4>

      <h5 className="mt-4 pt-2">Attribute View</h5>
      {attributeViews}

      <h5 className="mt-4 pt-2">Raw View</h5>
      <div className="row g-3">
        {[
          { id: 'collapseLevel1Api', label: 'Level 1', data: level1, query: '?level=1', defaultOpen: true },
          { id: 'collapseLevel2Api', label: 'Level 2', data: level2, query: '?level=2', defaultOpen: false },
          { id: 'collapseUncollatedApi', label: 'Uncollated', data: uncollated, query: '?collated=false', defaultOpen: false },
        ].map(({ id, label, data, query, defaultOpen }) => (
          <div className="col-12" key={id}>
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center position-relative">
                <button
                  className="btn btn-link text-decoration-none p-0 flex-grow-1 text-start text-black stretched-link"
                  type="button"
                  data-bs-toggle="collapse"
                  data-bs-target={`#${id}`}
                  aria-expanded={defaultOpen}
                >
                  <h6 className="mb-0">{label}: /collection/{digest}{query}</h6>
                </button>
                {base && (
                  <a
                    className="btn btn-secondary btn-sm"
                    href={`${base}/collection/${digest}${query}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ zIndex: 999 }}
                  >
                    <i className="bi bi-box-arrow-up-right me-2" />
                    API
                  </a>
                )}
              </div>
              <div id={id} className={`collapse ${defaultOpen ? 'show' : ''}`}>
                <div className="card-body">
                  <pre className="card card-body bg-light mb-0">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export { APICollectionView };
