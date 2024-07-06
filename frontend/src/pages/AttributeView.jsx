import { Link, useLoaderData, useParams } from "react-router-dom"
import { AttributeValue, LinkedAttributeDigest } from '../components/Attributes.jsx'
import { API_BASE } from '../utilities.jsx'
import { CollectionList } from '../components/ObjectLists.jsx'

const AttributeView = () => { 
    const content = useLoaderData()
    const { attribute, digest } = useParams()
    const api_url = `${API_BASE}/attribute/${attribute}/${digest}`
    const api_url_list = `${API_BASE}/attribute/${attribute}/${digest}/list`
    let results = content[0]
    let attribute_value = content[1]
  
    console.log("AttributeView attribute_value: " , attribute_value)
    console.log("AttributeView results: " , results)
    
    return (
      <div>
        <h1>Attribute: {attribute} 
        </h1>
        <div className="row align-items-center">
          <div className="col-md-1">API URL:</div>
          <div className="col"><Link to={api_url}>{api_url}</Link></div>
        </div>
        <div className="row align-items-center">
          <div className="col-md-1">Digest:</div>
          <div className="col">
            <LinkedAttributeDigest attribute={attribute} digest={digest}/>
          </div>
        </div>
        <div className="row align-items-center">
          <div className="col-md-1">Value:</div>
          <div className="col"><AttributeValue value={attribute_value} /></div>
        </div>
        <h2 className="mt-4">Containing collections:</h2>
        API URL: <Link to={api_url_list}>{api_url_list}</Link>
        <CollectionList collections={results}  clipboard={false}/>
      </div>
    )
  }

  export { AttributeView }