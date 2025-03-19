import { LinkedCollectionDigest } from "../components/ValuesAndDigests.jsx"
import { useLoaderData, Link } from "react-router-dom"
import { API_BASE } from "../utilities.jsx"


const ComparisonView =({ paramComparison }) => { 
    const loaderData = useLoaderData()
    const comparison = paramComparison || loaderData
    console.log("ComparisonView", comparison)
    const comp_str = JSON.stringify(comparison, null, 2)
    
    let api_url = `${API_BASE}/comparison/${comparison.digests.a}/${comparison.digests.b}`

    // Do some analysis for interpretation


  const getInterpretation = (comparison, attribute) => {
    const nSequencesA = comparison.array_elements.a[attribute]
    const nSequencesB = comparison.array_elements.b[attribute]
    const aNotB = comparison.array_elements.a[attribute] - comparison.array_elements.a_and_b[attribute]
    const bNotA = comparison.array_elements.b[attribute] - comparison.array_elements.a_and_b[attribute]
    let interpretation = ""
    let interpTerm = ""

    if (comparison.array_elements.a_and_b[attribute] == nSequencesA && comparison.array_elements.a_and_b[attribute] == nSequencesB) {
      interpretation = `The ${attribute} contents are identical.`
      interpTerm = "identical_content"
    } else if (comparison.array_elements.a_and_b[attribute] == nSequencesA && comparison.array_elements.a_and_b[attribute] < nSequencesB) {
      interpretation = `Collection B contains all ${nSequencesA} ${attribute} from collection A, and ${bNotA} additional.`
      interpTerm = "subset"
    } else if (comparison.array_elements.a_and_b[attribute] == nSequencesB && comparison.array_elements.a_and_b[attribute] < nSequencesA) {
      interpretation = `Collection A contains all ${nSequencesB} ${attribute} from collection B, and ${aNotB} additional.`
      interpTerm = "subset"
    } else if (comparison.array_elements.a_and_b[attribute] === 0){
      interpretation = `The collections' ${attribute} contents are disjoint.`
      interpTerm = "disjoint"
    } else if (comparison.array_elements.a_and_b[attribute] < nSequencesA && comparison.array_elements.a_and_b[attribute] < nSequencesB) {
      interpretation = `The collections' ${attribute} contents are partially overlapping; some are shared, and some are unique to each collection.`
      interpTerm = "partial_overlap"
    } else {
      interpretation = "This is hard for me to interpret."
    }
    return {interpretation, interpTerm}
  }

  const attributesToCheck = ["sequences", "names", "lengths", "name_length_pairs"]
  const interpretation = {}
  for (let attribute of attributesToCheck) {
    interpretation[attribute] = getInterpretation(comparison, attribute)
  }
  console.log(interpretation)
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

        <h2>Interpretation Summary</h2>        
          <div className="alert alert-success" name="Interpretation">
            <ul>
        {comparison.attributes.a_only.length === 0 && comparison.attributes.b_only.length === 0 && (
              <li>Attributes are identical. </li>
            )}
            <li>{interpretation["sequences"].interpretation}</li>
            <li>{interpretation["names"].interpretation}</li>
            <li>{interpretation["lengths"].interpretation}</li>
            <li>{interpretation["name_length_pairs"].interpretation}</li>
          </ul>
            </div>



        <h2>Details</h2>
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
          <div className="d-flex"  key={key}>
            <label className="col-sm-3 d-flex justify-content-end px-4">{key}:</label>{value}
          </div>
        ))}
        </div>

        <h3>Sequence order check</h3>
        <div className="row mb-3">
        <label className="col-sm-4 fw-bold">Are the elements in matching order?:</label>
        {Object.entries(comparison.array_elements.a_and_b_same_order).map(([key, value]) => (
          <div className="d-flex"  key={key}>
            <label className="col-sm-3 d-flex justify-content-end px-4">{key}:</label>{value !== null ? value.toString() : 'null'}
          </div>
        ))
        
        
        }
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
