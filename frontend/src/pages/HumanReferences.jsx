import { Link } from 'react-router-dom';
import { CompareTable } from '../components/CompareTable.jsx';
import { LinkedCollectionDigest } from '../components/ValuesAndDigests.jsx';

// A curated set of common human reference assemblies across providers, drawn
// from the Jungle collection hosted on the seqcol API. Digests are the current
// server digests (verified against jungle.json), so collection and comparison
// links resolve. To browse the full set of human references, use the Jungle.
const reference_digests = {
  'hg38 UCSC': 'a_WL8OC7sFJfjux5m11M2bKl0dYepA1x',
  'GRCh38 GENCODE': 'tmnbiAyj2fke68d_TYjq2g487US8C15r',
  'GRCh38 Ensembl': 'oLfPx0NOBKKXMIngGeQ4YewtU4Ge_wKz',
  'GRCh38.p14 NCBI': 'u1HyLgIlq8M_XvEwy0oGqAvKGHJMGtxH',
  'GRCh38 Broad': 'EiFob05aCWgVU_B_Ae0cypnQut3cxUP1',
  'hg19 UCSC': 'ThZcNYiLuWWL86NdJ8dvvJG15K9mW3Fo',
  'GRCh37 GENCODE': 'k4mLJvbFzZiw3o6SL8hh63V2u7AjDMrE',
  'hs37d5 1000G': 'Q3xii3AkJDCTXSO6Vg13kjbOutQu0KP9',
  'hg18 UCSC': 'ieWVCws5MC2QFRKgH9QcN3u5_Y_3hPG6',
};

function HumanReferencesView() {
  return (
    <div className='home mb-5'>
      <h4 className='fw-light'>Human Reference Genome Comparisons</h4>
      <p className='mt-3 text-muted'>
        A selection of common human reference assemblies from different providers,
        drawn from the{' '}
        <Link to='/jungle'>Jungle collection</Link>. Compare any pair below, or
        browse the full set of human (and mouse) references in the Jungle.
      </p>

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
                <td>
                  <LinkedCollectionDigest
                    digest={reference_digests[property]}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <CompareTable seqColDict={reference_digests} />
    </div>
  );
}

export { HumanReferencesView };
