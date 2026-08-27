import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore';
import { APINav } from '../components/APINav';
import { fetchCollectionLevels } from '../services/fetchData';
import type { SeqColLevel1, SeqColLevel2 } from '../types';
import {
  AttributeValue,
  LinkedAttributeDigest,
} from '../components/ValuesAndDigests';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';

const APICollectionView = () => {
  const { digest } = useParams();
  const [searchParams] = useSearchParams();
  const { apiUrl, probeApi } = useApiExplorerStore();
  // fetchCollectionLevels resolves to [level1, level2, uncollated].
  const [collection, setCollection] =
    useState<[SeqColLevel1, SeqColLevel2, SeqColLevel2] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Bootstrap's collapse plugin is gone; one panel open at a time, in state.
  const [openPanel, setOpenPanel] = useState<string | null>('level1');

  const urlParam = searchParams.get('url');
  const effectiveUrl = apiUrl || urlParam;

  useEffect(() => {
    const init = async () => {
      try {
        if (urlParam && !apiUrl) {
          await probeApi(urlParam);
        }
        const result = await fetchCollectionLevels(digest ?? '', effectiveUrl);
        setCollection(result);
      } catch (err) {
        setError(errorMessage(err));
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
        <div className="text-center py-12">
          <div className="spinner" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <APINav active="collections" />
        <div className="alert alert--danger">{error}</div>
      </div>
    );
  }

  if (!Array.isArray(collection) || collection.length < 3) {
    return (
      <div>
        <APINav active="collections" />
        <div className="alert alert--warning">Failed to load collection data.</div>
      </div>
    );
  }

  const level1 = collection[0];
  const level2 = collection[1];
  const uncollated = collection[2];
  const base = effectiveUrl?.replace(/\/+$/, '') || '';

  const attributeViews = Object.keys(level2).map((attribute) => (
    <div key={attribute}>
      <h6 className="mb-2 mt-6 font-medium">{attribute}</h6>
      <div className="kv">
        <div className="kv__term text-muted">Digest:</div>
        <div className="kv__value">
          <LinkedAttributeDigest attribute={attribute} digest={level1[attribute] ?? ''} />
        </div>
      </div>
      <div className="kv">
        <div className="kv__term text-muted">Value:</div>
        <div className="kv__value">
          <AttributeValue value={level2[attribute]} />
        </div>
      </div>
    </div>
  ));

  return (
    <div>
      <APINav active="collections" />

      <h4 className="font-light">Sequence Collection: {digest}</h4>

      <h5 className="mt-6 pt-2">Attribute View</h5>
      {attributeViews}

      <h5 className="mt-6 pt-2">Raw View</h5>
      <div className="flex flex-col gap-4">
        {[
          { id: 'level1', label: 'Level 1', data: level1, query: '?level=1' },
          { id: 'level2', label: 'Level 2', data: level2, query: '?level=2' },
          { id: 'uncollated', label: 'Uncollated', data: uncollated, query: '?collated=false' },
        ].map(({ id, label, data, query }) => (
          <div key={id}>
            <div className="card">
              <div className="card__header flex justify-between items-center gap-2">
                <button
                  className="btn--link no-underline flex-grow text-left text-strong"
                  type="button"
                  aria-expanded={openPanel === id}
                  onClick={() => setOpenPanel(openPanel === id ? null : id)}
                >
                  <h6 className="mb-0">
                    <Icon
                      name={openPanel === id ? 'chevron-down' : 'chevron-right'}
                      className="mr-1"
                    />
                    {label}: /collection/{digest}{query}
                  </h6>
                </button>
                {base && (
                  <a
                    className="btn btn--secondary btn--sm"
                    href={`${base}/collection/${digest}${query}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Icon name="external" className="mr-2" />
                    API
                  </a>
                )}
              </div>
              {openPanel === id && (
                <div className="card__body">
                  <pre className="code-block mb-0">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export { APICollectionView };
