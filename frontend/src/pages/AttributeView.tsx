import { useEffect } from 'react';
import { Link, useLoaderData, useParams, useSearchParams } from 'react-router-dom';
import {
  AttributeValue,
  LinkedAttributeDigest,
} from '../components/ValuesAndDigests';
import { API_BASE } from '../utilities';
import { CollectionList } from '../components/ObjectLists';
import { APINav } from '../components/APINav';
import { ExplorerApiContext } from '../hooks/useExplorerApi';
import { useApiExplorerStore } from '../stores/apiExplorerStore';

const AttributeView = () => {
  const content = useLoaderData() as unknown;
  const { attribute = '', digest = '' } = useParams();
  const [searchParams] = useSearchParams();
  const { apiUrl, probeApi } = useApiExplorerStore();
  // Set when the API Explorer links here: the API being explored.
  const urlParam = searchParams.get('url');

  // Keep the explorer's tabs pointing at this API, even on a fresh page load.
  useEffect(() => {
    if (urlParam && urlParam.replace(/\/+$/, '') !== apiUrl) {
      probeApi(urlParam).catch(() => {});
    }
  }, [urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!Array.isArray(content) || content.length < 2) {
    return <div className="alert alert--warning">Failed to load attribute data.</div>;
  }

  const base = (urlParam || API_BASE).replace(/\/+$/, '');
  const api_url = `${base}/attribute/collection/${attribute}/${digest}`;
  const api_url_list = `${base}/list/collection?${attribute}=${digest}`;
  const results = content[0] as { results?: string[] };
  const attribute_value = content[1];

  return (
    <ExplorerApiContext value={urlParam}>
      <div className='mb-12'>
        {urlParam && <APINav />}
        <h4 className='font-light'>Attribute: {attribute} </h4>
        <LinkedAttributeDigest attribute={attribute} digest={digest} />
        <p className='mt-4 text-muted'>
          The <span className='font-mono text-success-fg'>/attribute</span>{' '}
          endpoint lets you retrieve the value of a specific attribute of a
          sequence collection, given its digest.
        </p>
        {/* <hr /> */}
        <div className='kv'>
          <div className='kv__term text-muted'>API URL:</div>
          <div className='kv__value'>
            <Link to={api_url}>{api_url}</Link>
          </div>
        </div>
        <div className='kv'>
          <div className='kv__term text-muted'>Value:</div>
          <div className='kv__value'>
            <AttributeValue value={attribute_value} />
          </div>
        </div>
        <h5 className='mt-6'>Containing collections:</h5>
        <p className='mt-4 text-muted'>
          This uses the{' '}
          <span className='font-mono text-success-fg'>/list/collection</span>{' '}
          endpoint, passing the attribute name and digest to discover all
          collections with the attribute{' '}
          <span className='font-mono text-success-fg'>{attribute}</span> that
          have digest{' '}
          <span className='font-mono text-success-fg'>{digest}</span>.
        </p>
        API URL: <Link to={api_url_list}>{api_url_list}</Link>
        <CollectionList collections={results} />
      </div>
    </ExplorerApiContext>
  );
};

export { AttributeView };
