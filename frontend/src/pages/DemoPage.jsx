import { CompareTable } from '../components/CompareTable.jsx';
import { LinkedCollectionDigest } from '../components/ValuesAndDigests';

function DemoPage() {
    const demo_seqcol_digests = {
      base_collection: "fLf5M0BOIPIqcfbE6R8oYwxsy-PnoV32",
      different_names_collection: "TKB7n_14iKSFjljBA-TSVjeYpxPQe0-k",
      different_order_collection: "JPd9Y-hwnhGD7HPe3yka4Qtx2YsIL8tW",
      pair_swap_collection: "E6zGtGuc8wKYmCMw5gaLW3ppyXsoO6p4",
      subset_collection: "8aA37TYgiVohRqfRhXEeklIAXf2Rs8jw",
      swap_wo_coords_collection: "EkMSPx-_MdAzj2tWGfdFSVsuv03OznPn",
    }
  
  return <div>
    <h2>Demo sequence collection comparisons</h2>
      The server loads several demo FASTA files that showcase different comparisons.
      <table>
        <thead>
          <tr>
            <th>collection name</th>
            <th>digest</th>
          </tr>
        </thead>
        <tbody>
        {Object.keys(demo_seqcol_digests).map((property) => {
          return (
            <tr key={demo_seqcol_digests[property]}>
              <td>{property}</td>
              <td><LinkedCollectionDigest digest={demo_seqcol_digests[property]}/></td>
            </tr>
          )
        })}
        </tbody>
      </table>
      <CompareTable seqColList={Object.values(demo_seqcol_digests)}/>
    </div>
  
  }

export { DemoPage }
