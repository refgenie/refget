import { CompareTable } from '../components/CompareTable.jsx';
import { LinkedCollectionDigest } from '../components/ValuesAndDigests.jsx';

function DemoPage() {
  const demo_seqcol_digests = {
    base_collection: 'XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk',
    different_names_collection: 'QvT5tAQ0B8Vkxd-qFftlzEk2QyfPtgOv',
    different_order_collection: 'Tpdsg75D4GKCGEHtIiDSL9Zx-DSuX5V8',
    pair_swap_collection: 'UNGAdNDmBbQbHihecPPFxwTydTcdFKxL',
    subset_collection: 'sv7GIP1K0qcskIKF3iaBmQpaum21vH74',
    swap_wo_coords_collection: 'aVzHaGFlUDUNF2IEmNdzS_A8lCY0stQH',
  };

  return (
    <div className='home'>
      <h4 className='fw-light'>Demo Sequence Collection Comparisons</h4>
      <p className='text-muted mt-3'>
        The server loads several demo FASTA files that showcase different
        comparisons.
      </p>
      <table className='mt-4'>
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
                <td>
                  <LinkedCollectionDigest
                    digest={demo_seqcol_digests[property]}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <CompareTable seqColDict={demo_seqcol_digests} />
    </div>
  );
}

export { DemoPage };
