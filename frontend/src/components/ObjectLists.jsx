import { Link } from "react-router-dom"
import { useLoaderData } from "react-router-dom"


// Basic list of Sequence Collections
const CollectionList = ({collections}) => {
    const seqColList = collections || useLoaderData()[0]
    console.log("seqColList", seqColList)
  
    return (<>
      <div>
        <ul>
          {seqColList.results.map((seqCol) => (
            <li key={seqCol}>
              Collection: <Link to={`/collection/${seqCol}`} className="font-monospace">{seqCol}</Link>
            </li>
          ))}
        </ul>
      </div></>
    )
  }

const AttributeList = ({attributes}) => {
  const attrList = attributes || useLoaderData()[0]
  console.log("attrList", attrList)

  return (<>
    <div>
      <ul>
        {attrList.results?.map((attr) => (
          <li key={attr}>
            Attribute: <Link to={`/attribute/sorted_name_length_pairs/${attr}`}>{attr}</Link>
          </li>
        ))}
      </ul>
    </div></>
  )
}


// Basic list of Pangenomes
const PangenomeList = ({pangenomes}) => {
  const pangenomeList = pangenomes || useLoaderData()[1]
  console.log("pangenomeList", pangenomeList)

  return (<>
    <div>
      <ul>
        {pangenomeList.results?.map((pangenome) => (
          <li key={pangenome}>
            <Link to={`/pangenome/${pangenome}`}>{pangenome}</Link>
          </li>
        ))}
      </ul>
    </div></>
  )
}



  export { AttributeList, CollectionList, PangenomeList }
  