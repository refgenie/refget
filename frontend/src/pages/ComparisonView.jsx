import { LinkedCollectionDigest } from "../components/ValuesAndDigests.jsx"
import { useLoaderData, Link } from "react-router-dom"
import { API_BASE } from "../utilities.jsx"



const CoordSystemReport = ({message}) => {
  return (
    <div>
      <div className="alert alert-warning">
      <h3>Coordinate System</h3>
        <p>{message}</p>
      </div>
    </div>
  )
}

// Component to display the comparison between two collections
// ✅❔❌❔
const CoordinateSystemInterpretation = ({comparison}) => {
  const lengthsANotB = comparison.array_elements.a.lengths - comparison.array_elements.a_and_b.lengths
  const lengthsBNotA = comparison.array_elements.b.lengths - comparison.array_elements.a_and_b.lengths
  const namesANotB = comparison.array_elements.a.names - comparison.array_elements.a_and_b.names
  const namesBNotA = comparison.array_elements.b.names - comparison.array_elements.a_and_b.names
  const nlpANotB = comparison.array_elements.a.name_length_pairs - comparison.array_elements.a_and_b.name_length_pairs
  const nlpBNotA = comparison.array_elements.b.name_length_pairs - comparison.array_elements.a_and_b.name_length_pairs
  // If the name_length_pairs match, then the coordinate systems are identical
  if (nlpANotB === 0 && nlpBNotA === 0) {
    return <CoordSystemReport message="🟰The coordinate systems are identical"/>
  } else if (nlpANotB === 0 && nlpBNotA > 0) {  // If A nlp is a subset of B
    return <CoordSystemReport message="Collection A's coordinate system is a subset of B's."/>
  } else if (nlpANotB > 0 && nlpBNotA === 0) {  // If B nlp is a subset of A
    return <CoordSystemReport message="Collection B's coordinate system is a subset of A's."/>
  } else if (comparison.array_elements.a_and_b.name_length_pairs !== 0) {  // If there is some overlap
    return <CoordSystemReport message="The coordinate systems are partially overlapping."/>
  } else {  // If there is no overlap
    const msgArray = []
    msgArray.push("The coordinate systems are disjoint.")
    // If the lengths match and names match
    if (lengthsANotB === 0 && lengthsBNotA === 0 && namesANotB === 0 && namesBNotA === 0) {
      msgArray.push("⚠️ Name pair swap!")
    } else if (lengthsANotB === 0 && lengthsBNotA === 0) {  // If lengths match but names don't
      msgArray.push("✅ Lengths  match. ⚠️ Names don't match.")
    } else if (namesANotB === 0 && namesBNotA === 0) {  // If names match but lengths don't
      msgArray.push("✅ Names match. ⚠️ Lengths don't match.")
    }
    return <CoordSystemReport message={msgArray.join(" ")}/>
  }
  return <CoordSystemReport message="I'm not sure what's going on with the coordinate systems."/>
}



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
            <CoordinateSystemInterpretation comparison={comparison} />


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
