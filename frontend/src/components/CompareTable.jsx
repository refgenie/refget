import { Link } from "react-router-dom";
import compare from '../assets/compare.svg'

const CompareTable = ({seqColList}) => {  

    function buildCompareLinks(seqColList) {
      let header_cells = [];
      for (let i = 0; i < seqColList.length; i++) {
        header_cells.push(<th key={"header_col_"+i} className='rotated-text'><div>{seqColList[i]}</div></th>)
      }
      let header_row = <tr><th></th>{header_cells}</tr>;
  
      let link_rows = [];
      for (let i = 0; i < seqColList.length; i++) {
        let link_cells = []
        link_cells.push(<th className="text-end" key={"header_row_"+i}><Link to={`/collection/${seqColList[i]}`}>{seqColList[i]}</Link></th>)
        for (let j = 0; j < seqColList.length; j++) {
          link_cells.push(
            <td key={i + "vs" + j} className="text-center">{ j == i ? "=" : <Link
              to={`/comparison/${seqColList[i]}/${seqColList[j]}`}
              key={`${seqColList[i]}-${seqColList[j]}`}
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
      <h3>Comparison table</h3>
      {buildCompareLinks(seqColList)}
    </>
  }

export { CompareTable }