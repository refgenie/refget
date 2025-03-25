import { CompareTable } from '../components/CompareTable.jsx';
import { LinkedCollectionDigest } from '../components/ValuesAndDigests.jsx';

import reference_digests from '../assets/ref_fasta.json'

function HumanReferencesView() {
 
  return <div>
    <h2>Human reference genome comparisons</h2>
      The server hosts several demo common human references from different providers, which you can compare.
      <table>
        <thead>
          <tr>
            <th>collection name</th>
            <th>digest</th>
          </tr>
        </thead>
        <tbody>
        {Object.keys(reference_digests).map((property) => {
          return (
            <tr key={reference_digests[property]}>
              <td>{property}</td>
              <td><LinkedCollectionDigest digest={reference_digests[property]}/></td>
            </tr>
          )
        })}
        </tbody>
      </table>
      <CompareTable seqColDict={reference_digests}/>
    </div>
  
  }

export { HumanReferencesView }
