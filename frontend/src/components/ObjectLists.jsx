import { Link } from 'react-router-dom';
import { useLoaderData } from 'react-router-dom';

// Basic list of Sequence Collections
const CollectionList = ({ collections }) => {
  const seqColList = collections || useLoaderData()[0];

  return (
    <>
      <div>
        <ul>
          {seqColList.results.map((seqCol) => (
            <li key={seqCol}>
              Collection:{' '}
              <Link to={`/collection/${seqCol}`} className='font-monospace'>
                {seqCol}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
};

const AttributeList = ({ attributeName, attributeDigests }) => {
  const attrList = attributeDigests || useLoaderData()[0];

  return (
    <>
      <div>
        <ul>
          {attrList.results?.map((attr) => (
            <li key={attr}>
              Attribute:{' '}
              <Link to={`/attribute/${attributeName}/${attr}`}>{attr}</Link>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
};

// Basic list of Pangenomes
const PangenomeList = ({ pangenomes }) => {
  const pangenomeList = pangenomes || useLoaderData()[1];

  return (
    <>
      <div>
        <ul>
          {pangenomeList.results?.map((pangenome) => (
            <li key={pangenome}>
              <Link to={`/pangenome/${pangenome}`}>{pangenome}</Link>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
};

export { AttributeList, CollectionList, PangenomeList };
