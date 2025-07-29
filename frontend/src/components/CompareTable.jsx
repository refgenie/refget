import { Link } from "react-router-dom";
import compare from '../assets/compare.svg'

const CompareTable = ({seqColDict}) => {  
    const seqColNames = Object.keys(seqColDict)
    const seqColDigests = Object.values(seqColDict)

    function buildCompareLinks(seqColDigests) {
      let header_cells = [];
      for (let i = 0; i < seqColDigests.length; i++) {
        header_cells.push(<th key={"header_col_"+i} className='rotated-text'><div>{seqColNames[i]}</div></th>)
      }
      let header_row = <tr><th></th>{header_cells}</tr>;
  
      let link_rows = [];
      for (let i = 0; i < seqColDigests.length; i++) {
        let link_cells = []
        link_cells.push(<th className="text-end" key={"header_row_"+i}><Link to={`/collection/${seqColDigests[i]}`}>{seqColNames[i]}</Link></th>)
        for (let j = 0; j < seqColDigests.length; j++) {
          link_cells.push(
            <td key={i + "vs" + j} className="text-center">{ j == i ? "=" : <Link
              to={`/scim/${seqColDigests[i]}/${seqColDigests[j]}`}
              key={`${seqColDigests[i]}-${seqColDigests[j]}`}
            ><img src={compare} alt="Compare" width="50" className="compare"/>
            </Link>}</td>
          );
        }
        link_rows.push(<tr key={"row_" + i}>{link_cells}</tr>);
      }
      let table = <table border="0">
        <thead>{header_row}</thead>
        <tbody>{link_rows}</tbody>
      </table>;
      return table;
    }
  
    return  <>     
      <h5 className='mt-4 pt-2'>Comparison table</h5>
      {buildCompareLinks(seqColDigests)}
    </>
  }

export { CompareTable }
