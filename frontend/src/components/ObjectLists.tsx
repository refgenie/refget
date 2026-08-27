import { Link } from 'react-router-dom';
import { useLoaderData } from 'react-router-dom';

interface Listing {
  results?: string[];
}

// Basic list of Sequence Collections
const CollectionList = ({ collections }: { collections?: Listing }) => {
  const loaderData = useLoaderData() as Listing[];
  const seqColList = collections || loaderData[0];

  return (
    <>
      <div>
        <ul>
          {seqColList.results?.map((seqCol) => (
            <li key={seqCol}>
              Collection:{' '}
              <Link to={`/collection/${seqCol}`} className='font-mono'>
                {seqCol}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
};

const AttributeList = ({
  attributeName,
  attributeDigests,
}: {
  attributeName: string;
  attributeDigests?: Listing;
}) => {
  const loaderData = useLoaderData() as Listing[];
  const attrList = attributeDigests || loaderData[0];

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
const PangenomeList = ({ pangenomes }: { pangenomes?: Listing }) => {
  const loaderData = useLoaderData() as Listing[];
  const pangenomeList = pangenomes || loaderData[1];

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
