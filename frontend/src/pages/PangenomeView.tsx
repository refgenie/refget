import { Link, useLoaderData, useParams } from 'react-router-dom';
import {
  AttributeValue,
} from '../components/ValuesAndDigests';

import { API_BASE } from '../utilities';

// Basic View of a Pangenome object
const PangenomeView = () => {
  const pangenome = useLoaderData();
  const { digest } = useParams();

  if (!Array.isArray(pangenome) || pangenome.length < 3) {
    return <div className="alert alert--warning">Failed to load pangenome data.</div>;
  }

  const level1 = pangenome[0];
  const level2 = pangenome[1];
  const itemwise = pangenome[2];

  const api_url_level1 = `${API_BASE}/pangenome/${digest}?level=1`;
  const api_url_level2 = `${API_BASE}/pangenome/${digest}?level=2`;
  const api_url_level3 = `${API_BASE}/pangenome/${digest}?level=3`;
  const api_url_level4 = `${API_BASE}/pangenome/${digest}?level=4`;

  return (
    <>
      <div>
        <h2>Pangenome: {digest}</h2>
        <hr />
        <h2>API URLs</h2>
        <ul>
          <li>
            Level 1: <Link to={api_url_level1}>{api_url_level1}</Link>
          </li>
          <li>
            Level 2: <Link to={api_url_level2}>{api_url_level2}</Link>
          </li>
          <li>
            Level 3: <Link to={api_url_level3}>{api_url_level3}</Link>
          </li>
          <li>
            Level 4: <Link to={api_url_level4}>{api_url_level4}</Link>
          </li>
        </ul>

        <h2>Resident sequence collections:</h2>
        <table>
          <thead>
            <tr className='m-12'>
              <th>Name</th>
              <th>Digest</th>
            </tr>
          </thead>
          <tbody className='m-12'>
            {itemwise.collections.map((seqCol: { name: string; collection: string }) => (
              <tr key={seqCol.name}>
                <td className='px-2'>{seqCol.name}</td>
                <td>
                  <Link to={`/collection/${seqCol.collection}`}>
                    {seqCol.collection}
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2>Attributes:</h2>
        <PangenomeAttributeListView level1={level1} level2={level2} />

        <h2>Raw view:</h2>
        <h3>Level 1:</h3>
        <pre className='card card__body bg-surface-muted'>
          {JSON.stringify(level1, null, 2)}
        </pre>
        <h3>Level 2:</h3>
        <pre className='card card__body bg-surface-muted'>
          {JSON.stringify(level2, null, 2)}
        </pre>
      </div>
    </>
  );
};

//         <h2>Compare table:</h2>
{
  /* <CompareTable seqColList={pangenome.level2.collections}/> */
}

const PangenomeAttributeListView = ({
  level1,
  level2,
}: {
  level1: Record<string, string>;
  level2: Record<string, unknown>;
}) => {
  const attribute_list_views = [];
  for (const attribute in level2) {
    attribute_list_views.push(
      <div key={attribute}>
        <h5 className='mb-2 mt-4'>{attribute}</h5>
        <div className='kv'>
          <div className='kv__term'>Digest:</div>
          <div className='kv__value'>{level1[attribute]}</div>
        </div>
        <div className='kv'>
          <div className='kv__term'>Value:</div>
          <div className='kv__value'>
            <AttributeValue value={level2[attribute]} />
          </div>
        </div>
      </div>,
    );
  }
  return attribute_list_views;
};

export { PangenomeView };
