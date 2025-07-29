import { CompareTable } from '../components/CompareTable.jsx';
import { LinkedCollectionDigest } from '../components/ValuesAndDigests.jsx';

import reference_digests from '../assets/ref_fasta.json'

function HumanReferencesView() {
 
  return <div className='home mb-5'>
    <h4 className='fw-light'>Human Reference Genome Comparisons</h4>
    <p className='mt-3 text-muted'>The server hosts several demo common human references from different providers, which you can compare.</p>  
      
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
