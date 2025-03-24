

// TODO: fetch this from pephub

import hprc from '../assets/hprc.json'
import { LinkedCollectionDigest } from '../components/ValuesAndDigests.jsx'



const HPRCGenomes = () => {

    // Build a table of genomes from the HPRC   
    console.log("Building HPRC genomes table...")
    console.log(Object.keys(hprc[0]))
    let header_cells = []
    let content_rows = []
    // for (let i of Object.keys(hprc[0])) {
    //     header_cells.push(<th key={"header_col_"+i}>{i} </th>)
    // }
    header_cells.push(<th>Assembly</th>)
    header_cells.push(<th>Accession</th>)
    header_cells.push(<th className="px-3">Seqcol digest</th>)

    for (let j of hprc) {
        let row_cells = []
        row_cells.push(<td>{j.sample_name}</td>)
        row_cells.push(<td><a href={j.assembly_link}>{j.assembly_accession}</a></td>)
        row_cells.push(<td className="px-3"><LinkedCollectionDigest digest={j.seqcol_digest}/></td>)
        content_rows.push(<tr key={j["name"]}>{row_cells}</tr>)

    }
    let header_row = <tr>{header_cells}</tr>;
    let table = <table border="0">
        <thead>{header_row}</thead>
        <tbody>{content_rows}</tbody>
    </table>;


    return (
        <div>
            <h2>Some genomes from the HPRC</h2>
            {table}
        </div>
    )

}

export { HPRCGenomes }