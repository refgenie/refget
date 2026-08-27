import { Link, useLoaderData, useParams } from 'react-router-dom';
import {
  AttributeValue,
  LinkedAttributeDigest,
} from '../components/ValuesAndDigests';
import { API_BASE } from '../utilities';
import { CollectionList } from '../components/ObjectLists';

const AttributeView = () => {
  const content = useLoaderData() as unknown;
  const { attribute = '', digest = '' } = useParams();

  if (!Array.isArray(content) || content.length < 2) {
    return <div className="alert alert--warning">Failed to load attribute data.</div>;
  }

  const api_url = `${API_BASE}/attribute/collection/${attribute}/${digest}`;
  const api_url_list = `${API_BASE}/list/collection?${attribute}=${digest}`;
  const results = content[0] as { results?: string[] };
  const attribute_value = content[1];

  return (
    <div className='mb-12'>
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
  );
};

export { AttributeView };
