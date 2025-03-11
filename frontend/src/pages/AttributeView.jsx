import { Link, useLoaderData, useParams } from "react-router-dom"
import { AttributeValue, LinkedAttributeDigest } from '../components/ValuesAndDigests.jsx'
import { API_BASE } from '../utilities.jsx'
import { CollectionList } from '../components/ObjectLists.jsx'

const AttributeView = () => { 
    const content = useLoaderData()
    const { attribute, digest } = useParams()
    const api_url = `${API_BASE}/attribute/collection/${attribute}/${digest}`
    const api_url_list = `${API_BASE}/list/collections/${attribute}/${digest}`
    let results = content[0]
    let attribute_value = content[1]
  
    console.log("AttributeView attribute_value: " , attribute_value)
    console.log("AttributeView results: " , results)
    
    return (
      <div>
        <h2>Attribute: {attribute} </h2> <LinkedAttributeDigest attribute={attribute} digest={digest}/>
        <p className="text-muted fs-6">
          The <span className="font-monospace text-success">/attribute</span> endpoint lets you retrieve
          the value of a specific attribute of a sequence collection, given its digest.
        </p>
        <hr/>
        <div className="row align-items-center">
        <div className="row align-items-center">
          <div className="col-md-1 text-secondary">API URL:</div>
          <div className="col"><Link to={api_url}>{api_url}</Link></div>
        </div>
        </div>
        <div className="row align-items-center">
          <div className="col-md-1 text-secondary">Value:</div>
          <div className="col"><AttributeValue value={attribute_value} /></div>
        </div>
        <h2 className="mt-4">Containing collections:</h2>
        <p className="text-muted fs-6">
          This uses the <span className="font-monospace text-success">/list/collections</span> endpoint,
          passing the attribute name and digest to discover all collections 
          with the attribute <span className="font-monospace text-success">{attribute}</span> that 
          have digest <span className="font-monospace text-success">{digest}</span>.
        </p>
        API URL: <Link to={api_url_list}>{api_url_list}</Link>
        <CollectionList collections={results}  clipboard={false}/>
      </div>
    )
  }

  export { AttributeView }