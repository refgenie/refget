import { LinkedCollectionDigest } from "../components/ValuesAndDigests.jsx"
import { useLoaderData, Link } from "react-router-dom"
import { API_BASE } from "../utilities.jsx"


const ComparisonView =() => { 
    const comparison = useLoaderData()
    console.log("ComparisonView", comparison)
    const comp_str = JSON.stringify(comparison, null, 2)
    
    let api_url = `${API_BASE}/comparison/${comparison.digests.a}/${comparison.digests.b}`
  
    return (
      <div>
        <h2>Comparison</h2>
        <h3>Collections being compared</h3>
        <div className="d-flex">
          <label className="col-sm-3 d-flex fw-bold justify-content-end px-4">Digest A:</label>
          <LinkedCollectionDigest digest={comparison.digests.a}/>
          </div>
        <div className="d-flex">
          <label className="col-sm-3 d-flex fw-bold justify-content-end px-4">Digest B:</label>
          <LinkedCollectionDigest digest={comparison.digests.b}/>
        </div>
        <h3>Attributes</h3>
        <div className="d-flex">
        <label className="col-sm-3 d-flex fw-bold justify-content-end px-4">Found in collection A only:</label>
        {comparison.attributes.a_only != "" ? comparison.attributes.a_only.join(', ') : <span className='text-muted'>None</span>}
        </div>
        <div className="d-flex">
        <label className="col-sm-3 d-flex fw-bold justify-content-end px-4">Found in collection B only:</label>
        {comparison.attributes.b_only != "" ? comparison.attributes.b_only.join(', ') : <span className='text-muted'>None</span>}
        </div>
        <div className="d-flex">
        <label className="col-sm-3 d-flex fw-bold justify-content-end px-4">Found in both:</label>
        {comparison.attributes.a_and_b != "" ? comparison.attributes.a_and_b.join(', ') : <span className='text-muted'>None</span>}
        </div>

  
        <h3>Array Elements</h3>
        <div className="row mb-3">
        <label className="col-sm-4 fw-bold">Number of elements found in both:</label>
        {Object.entries(comparison.array_elements.a_and_b).map(([key, value]) => (
          <div className="d-flex">
            <label className="col-sm-3 d-flex justify-content-end px-4">{key}:</label>{value}
          </div>
        ))}
        </div>

        <h2>Raw view:</h2>
        API URL: <Link to={api_url}>{api_url}</Link><br/>
        <pre className="card card-body bg-light">
        {comp_str}
        </pre>
      </div>
    )
  
  }

export { ComparisonView }
