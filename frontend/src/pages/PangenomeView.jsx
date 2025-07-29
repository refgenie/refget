import { Link, useLoaderData, useParams } from 'react-router-dom';
import {
  AttributeValue,
  LinkedAttributeDigest,
} from '../components/ValuesAndDigests.jsx';

import { API_BASE } from '../utilities.jsx';

// Basic View of a Pangenome object
const PangenomeView = ({ params }) => {
  const pangenome = useLoaderData();
  const { digest } = useParams();

  let level1 = pangenome[0];
  let level2 = pangenome[1];
  let itemwise = pangenome[2];

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
            <tr className='m-5'>
              <th>Name</th>
              <th>Digest</th>
            </tr>
          </thead>
          <tbody className='m-5'>
            {itemwise.collections.map((seqCol) => (
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
        <pre className='card card-body bg-light'>
          {JSON.stringify(level1, null, 2)}
        </pre>
        <h3>Level 2:</h3>
        <pre className='card card-body bg-light'>
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

const PangenomeAttributeListView = ({ level1, level2 }) => {
  let attribute_list_views = [];
  for (let attribute in level2) {
    attribute_list_views.push(
      <div key={attribute}>
        <h5 className='mb-2 mt-3'>{attribute}</h5>
        <div className='row align-items-center'>
          <div className='col-md-1 '>Digest:</div>
          <div className='col'>{level1[attribute]}</div>
        </div>
        <div className='row align-items-center'>
          <div className='col-md-1 '>Value:</div>
          <div className='col'>
            <AttributeValue value={level2[attribute]} />
          </div>
        </div>
      </div>,
    );
  }
  return attribute_list_views;
};

export { PangenomeView };
