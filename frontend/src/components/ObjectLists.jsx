import { Link } from "react-router-dom"

// Basic list of Sequence Collections
const CollectionList = ({collections}) => {
    const seqColList = collections || useLoaderData()[0]
    console.log("CollectionList", CollectionList)
  
    return (<>
      <div>
        <ul>
          {seqColList.items.map((seqCol) => (
            <li key={seqCol}>
              Collection: <Link to={`/collection/${seqCol}`} className="font-monospace">{seqCol}</Link>
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
        {pangenomeList.items.map((pangenome) => (
          <li key={pangenome}>
            <Link to={`/pangenome/${pangenome}`}>{pangenome}</Link>
          </li>
        ))}
      </ul>
    </div></>
  )
}



  export { CollectionList, PangenomeList }
  