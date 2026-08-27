import { Link } from 'react-router-dom';
import compare from '../assets/compare.svg';

interface CompareTableProps {
  /** Display name -> collection digest. */
  seqColDict: Record<string, string>;
}

const CompareTable = ({ seqColDict }: CompareTableProps) => {
  const seqColNames = Object.keys(seqColDict);
  const seqColDigests = Object.values(seqColDict);

  function buildCompareLinks(digests: string[]) {
    const header_cells = [];
    for (let i = 0; i < digests.length; i++) {
      header_cells.push(
        <th key={'header_col_' + i} className='table__head--rotated'>
          <div className='table__head-label'>{seqColNames[i]}</div>
        </th>,
      );
    }
    const header_row = (
      <tr>
        <th></th>
        {header_cells}
      </tr>
    );

    const link_rows = [];
    for (let i = 0; i < digests.length; i++) {
      const link_cells = [];
      link_cells.push(
        <th className='text-right' key={'header_row_' + i}>
          <Link to={`/collection/${digests[i]}`}>{seqColNames[i]}</Link>
        </th>,
      );
      for (let j = 0; j < digests.length; j++) {
        link_cells.push(
          <td key={i + 'vs' + j} className='text-center'>
            {j === i ? (
              '='
            ) : (
              <Link
                to={`/compare/${digests[i]}/${digests[j]}`}
                key={`${digests[i]}-${digests[j]}`}
              >
                <img
                  src={compare}
                  alt='Compare'
                  width='50'
                  className='compare-icon'
                />
              </Link>
            )}
          </td>,
        );
      }
      link_rows.push(<tr key={'row_' + i}>{link_cells}</tr>);
    }
    return (
      <table className='table table--borderless'>
        <thead>{header_row}</thead>
        <tbody>{link_rows}</tbody>
      </table>
    );
  }

  return (
    <>
      <h5 className='text-lg mt-6 pt-2'>Comparison table</h5>
      {buildCompareLinks(seqColDigests)}
    </>
  );
};

export { CompareTable };
