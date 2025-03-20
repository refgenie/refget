import { LinkedCollectionDigest } from "../components/ValuesAndDigests.jsx"
import { useLoaderData, Link } from "react-router-dom"
import { API_BASE } from "../utilities.jsx"


const CoordSystemReport = ({ messageArray }) => {
  return (
    <div className="alert alert-warning">
      <h3 className="alert-heading">
        Coordinate System<span 
          className="ms-2 badge bg-secondary text-white" 
          data-bs-toggle="tooltip" 
          data-bs-placement="right"
          title="This assessment reports on the compatibility of the names and lengths of the sequences, without regard to sequence content."
          style={{ cursor: 'pointer', fontSize: '0.7rem' }}
        >
          ?
        </span>
      </h3>
      <hr />
      <ul>{messageArray.map((msg, index) => (<li key={index}>{msg}</li>))}</ul>
    </div>
  );
};

const SequencesReport = ({messageArray}) => {
  return (
    <div className="alert alert-warning">
      <h3 className="alert-heading">
        Sequences<span 
          className="ms-2 badge bg-secondary text-white" 
          data-bs-toggle="tooltip" 
          data-bs-placement="right"
          title="This assessment reports on the sequences only, without regard to their names."
          style={{ cursor: 'pointer', fontSize: '0.7rem' }}
        >
          ?
        </span>
      </h3>
      <hr />
      <ul>{messageArray.map((msg, index) => (<li key={index}>{msg}</li>))}</ul>
    </div>
  );
};



// Component to display the comparison between two collections
// ✅❔❌❔
const coordinateSystemInterpretation = (comparison) => {
  const lengthsANotB = comparison.array_elements.a.lengths - comparison.array_elements.a_and_b.lengths
  const lengthsBNotA = comparison.array_elements.b.lengths - comparison.array_elements.a_and_b.lengths
  const namesANotB = comparison.array_elements.a.names - comparison.array_elements.a_and_b.names
  const namesBNotA = comparison.array_elements.b.names - comparison.array_elements.a_and_b.names
  const nlpANotB = comparison.array_elements.a.name_length_pairs - comparison.array_elements.a_and_b.name_length_pairs
  const nlpBNotA = comparison.array_elements.b.name_length_pairs - comparison.array_elements.a_and_b.name_length_pairs
  const msgArray = []
  // If the name_length_pairs match, then the coordinate systems are identical
  if (nlpANotB === 0 && nlpBNotA === 0) {
    msgArray.push("🟰 The coordinate systems are identical")
  } else if (nlpANotB === 0 && nlpBNotA > 0) {  // If A nlp is a subset of B
    msgArray.push("Collection A's coordinate system is a subset of B's.")
  } else if (nlpANotB > 0 && nlpBNotA === 0) {  // If B nlp is a subset of A
    msgArray.push("Collection B's coordinate system is a subset of A's.")
  } else if (comparison.array_elements.a_and_b.name_length_pairs !== 0) {  // If there is some overlap
    msgArray.push("The coordinate systems are partially overlapping.")
  } else {  // If there is no overlap
    msgArray.push("The coordinate systems are disjoint.")
    // If the lengths match and names match
    if (lengthsANotB === 0 && lengthsBNotA === 0 && namesANotB === 0 && namesBNotA === 0) {
      msgArray.push("⚠️ Name pair swap!")
    } else if (lengthsANotB === 0 && lengthsBNotA === 0) {  // If lengths match but names don't
      msgArray.push("✅ Lengths  match. ⚠️ Names don't match.")
    } else if (namesANotB === 0 && namesBNotA === 0) {  // If names match but lengths don't
      msgArray.push("✅ Names match. ⚠️ Lengths don't match.")
    }
  }
  // msgArray.push("I'm not sure what's going on with the coordinate systems.")
  return msgArray
}

const LinkToLocalComparison = ({ comparison }) => {
  const base64encodedComparison = btoa(JSON.stringify(comparison));
  return (
    <a 
      href={`/comparison?val=${base64encodedComparison}`} 
      title="View this comparison in Interpretation Module"
      className="text-decoration-none"
      >
      <i className="bi bi-search"> View Interpretation Module</i>
    </a>
  );
}


const ComparisonView =({ paramComparison }) => { 
    const loaderData = useLoaderData()
    const comparison = paramComparison || loaderData
    console.log("ComparisonView", comparison)
    const comp_str = JSON.stringify(comparison, null, 2)
    
    let api_url = `${API_BASE}/comparison/${comparison.digests.a}/${comparison.digests.b}`

    // Do some analysis for interpretation

// ✅❔❌
  const getInterpretation = (comparison, attribute) => {
    const nSequencesA = comparison.array_elements.a[attribute]
    const nSequencesB = comparison.array_elements.b[attribute]
    const aNotB = comparison.array_elements.a[attribute] - comparison.array_elements.a_and_b[attribute]
    const bNotA = comparison.array_elements.b[attribute] - comparison.array_elements.a_and_b[attribute]
    const orderCheck = comparison.array_elements.a_and_b_same_order[attribute]

    let interpTerm = ""
    const msgArray = []

    if (comparison.array_elements.a_and_b[attribute] == nSequencesA && comparison.array_elements.a_and_b[attribute] == nSequencesB) {
      msgArray.push(`🟰 The ${attribute} contents are identical.`)
      if (orderCheck === true) {
        msgArray.push("✅ The elements are in the same order.")
      } else if (orderCheck === false) {
        msgArray.push("❌ The elements are in different order.")
      }
      interpTerm = "identical_content"
    } 
    if (comparison.array_elements.a_and_b[attribute] == nSequencesA && comparison.array_elements.a_and_b[attribute] < nSequencesB) {
      msgArray.push(`Collection B contains all ${nSequencesA} ${attribute} from collection A, and ${bNotA} additional.`)
      interpTerm = "subset"
    }
     if (comparison.array_elements.a_and_b[attribute] == nSequencesB && comparison.array_elements.a_and_b[attribute] < nSequencesA) {
      msgArray.push(`Collection A contains all ${nSequencesB} ${attribute} from collection B, and ${aNotB} additional.`)
      interpTerm = "subset"
    } 
    if (comparison.array_elements.a_and_b[attribute] === 0){
      msgArray.push(`The collections' ${attribute} contents are disjoint.`)
      interpTerm = "disjoint"
    } else if (comparison.array_elements.a_and_b[attribute] < nSequencesA && comparison.array_elements.a_and_b[attribute] < nSequencesB) {
      msgArray.push(`The collections' ${attribute} contents are partially overlapping; some are shared, and some are unique to each collection.`)
      interpTerm = "partial_overlap"
    }
    
    return msgArray
  }

  const attributesToCheck = ["sequences", "names", "lengths", "name_length_pairs"]
  const interpretation = {}
  for (let attribute of attributesToCheck) {
    interpretation[attribute] = getInterpretation(comparison, attribute)
  }
  // console.log(interpretation)
  console.log("Comparison:", comparison)
  const coordSystemMessages = coordinateSystemInterpretation(comparison)

    return (
      <div>
        <h2>Comparison</h2>
        <LinkToLocalComparison comparison={comparison} />
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
            <div className="container-fluid">
              <div className="row">
                <div className="col-md-6">
                <SequencesReport messageArray={interpretation["sequences"]} />
                </div>
                <div className="col-md-6">
                <CoordSystemReport messageArray={coordSystemMessages}/>
                </div>
              </div>
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
