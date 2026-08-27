import { useState } from 'react';
import { LinkedCollectionDigest } from '../components/ValuesAndDigests';
import { useLoaderData } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { ReportCard } from '../components/ReportCard';

import { API_BASE, encodeToBase64 } from '../utilities';
import { Icon } from '../components/common/Icon';
import type { ComparisonResult } from '../types';

// Component to display the comparison between two collections
// ✅❔❌❔
const coordinateSystemInterpretation = (comparison: ComparisonResult) => {
  if (!comparison?.array_elements?.a_count || !comparison?.array_elements?.b_count || !comparison?.array_elements?.a_and_b_count) {
    return ['Unable to interpret: incomplete comparison data'];
  }

  const lengthsANotB =
    comparison.array_elements.a_count.lengths -
    comparison.array_elements.a_and_b_count.lengths;
  const lengthsBNotA =
    comparison.array_elements.b_count.lengths -
    comparison.array_elements.a_and_b_count.lengths;
  const namesANotB =
    comparison.array_elements.a_count.names - comparison.array_elements.a_and_b_count.names;
  const namesBNotA =
    comparison.array_elements.b_count.names - comparison.array_elements.a_and_b_count.names;
  const nlpANotB =
    comparison.array_elements.a_count.name_length_pairs -
    comparison.array_elements.a_and_b_count.name_length_pairs;
  const nlpBNotA =
    comparison.array_elements.b_count.name_length_pairs -
    comparison.array_elements.a_and_b_count.name_length_pairs;
  const msgArray = [];
  // If the name_length_pairs match, then the coordinate systems are identical
  if (nlpANotB === 0 && nlpBNotA === 0) {
    msgArray.push('🟰 The coordinate systems are identical');
    msgArray.push('✅ Names match. ✅ Lengths match.');
  } else if (nlpANotB === 0 && nlpBNotA > 0) {
    // If A nlp is a subset of B
    msgArray.push("Collection A's coordinate system is a subset of B's.");
  } else if (nlpANotB > 0 && nlpBNotA === 0) {
    // If B nlp is a subset of A
    msgArray.push("Collection B's coordinate system is a subset of A's.");
  } else if (comparison.array_elements.a_and_b_count.name_length_pairs !== 0) {
    // If there is some overlap
    msgArray.push('The coordinate systems are partially overlapping.');
  } else {
    // If there is no overlap
    msgArray.push('The coordinate systems are disjoint.');
    // If the lengths match and names match
    if (
      lengthsANotB === 0 &&
      lengthsBNotA === 0 &&
      namesANotB === 0 &&
      namesBNotA === 0
    ) {
      msgArray.push('⚠️ Name pair swap!');
    } else if (lengthsANotB === 0 && lengthsBNotA === 0) {
      // If lengths match but names don't
      msgArray.push("✅ Lengths  match. ⚠️ Names don't match.");
    } else if (namesANotB === 0 && namesBNotA === 0) {
      // If names match but lengths don't
      msgArray.push("✅ Names match. ⚠️ Lengths don't match.");
    }
  }
  // msgArray.push("I'm not sure what's going on with the coordinate systems.")
  return msgArray;
};

const LinkToLocalComparison = ({ comparison }: { comparison: ComparisonResult }) => {
  const [copied, setCopied] = useState(false);
  const base64encodedComparison = encodeToBase64(JSON.stringify(comparison));
  return (
    <button
      className='btn btn--secondary btn--sm'
      onClick={() => {
        navigator.clipboard.writeText(
          `${window.location.origin}/compare?val=${base64encodedComparison}`,
        );
        setCopied(true);
        setTimeout(() => {
          setCopied(false);
        }, 2000);
      }}
    >
      {copied ? (
        <>
          <Icon name="check" className="mr-2" />
          Copied!
        </>
      ) : (
        <>
          <Icon name="clipboard" className="mr-2" />
          Result URL
        </>
      )}
    </button>
  );
};

const ComparisonView = ({ paramComparison }: { paramComparison?: ComparisonResult | null }) => {
  const loaderData = useLoaderData() as ComparisonResult | null;
  const comparison = paramComparison || loaderData;

  if (!comparison || !comparison.digests || !comparison.array_elements) {
    return (
      <div className='alert alert--warning mt-4' role='alert'>
        Invalid comparison data. The response may be malformed or incomplete.
      </div>
    );
  }

  const comp_str = JSON.stringify(comparison, null, 2);

  const api_url = `${API_BASE}/comparison/${comparison.digests.a}/${comparison.digests.b}`;

  // Do some analysis for interpretation

  // ✅❔❌
  const getInterpretation = (comparison: ComparisonResult, attribute: string) => {
    if (
      comparison.array_elements.a_count?.[attribute] == null ||
      comparison.array_elements.b_count?.[attribute] == null ||
      comparison.array_elements.a_and_b_count?.[attribute] == null
    ) {
      return [`Unable to interpret: missing ${attribute} data`];
    }

    const nSequencesA = comparison.array_elements.a_count[attribute];
    const nSequencesB = comparison.array_elements.b_count[attribute];
    const aNotB =
      comparison.array_elements.a_count[attribute] -
      comparison.array_elements.a_and_b_count[attribute];
    const bNotA =
      comparison.array_elements.b_count[attribute] -
      comparison.array_elements.a_and_b_count[attribute];
    const orderCheck = comparison.array_elements.a_and_b_same_order[attribute];

    const msgArray = [];

    if (
      comparison.array_elements.a_and_b_count[attribute] === nSequencesA &&
      comparison.array_elements.a_and_b_count[attribute] === nSequencesB
    ) {
      msgArray.push(`🟰 The ${attribute} contents are identical.`);
      if (orderCheck === true) {
        msgArray.push('✅ The elements are in the same order.');
      } else if (orderCheck === false) {
        msgArray.push('❌ The elements are in different order.');
      }
    }
    if (
      comparison.array_elements.a_and_b_count[attribute] === nSequencesA &&
      comparison.array_elements.a_and_b_count[attribute] < nSequencesB
    ) {
      msgArray.push(
        `Collection B contains all ${nSequencesA} ${attribute} from collection A, and ${bNotA} additional.`,
      );
    }
    if (
      comparison.array_elements.a_and_b_count[attribute] === nSequencesB &&
      comparison.array_elements.a_and_b_count[attribute] < nSequencesA
    ) {
      msgArray.push(
        `Collection A contains all ${nSequencesB} ${attribute} from collection B, and ${aNotB} additional.`,
      );
    }
    if (comparison.array_elements.a_and_b_count[attribute] === 0) {
      msgArray.push(`The collections' ${attribute} contents are disjoint.`);
    } else if (
      comparison.array_elements.a_and_b_count[attribute] < nSequencesA &&
      comparison.array_elements.a_and_b_count[attribute] < nSequencesB
    ) {
      msgArray.push(
        `The collections' ${attribute} contents are partially overlapping; some are shared, and some are unique to each collection.`,
      );
    }

    return msgArray;
  };

  const attributesToCheck = [
    'sequences',
    'names',
    'lengths',
    'name_length_pairs',
  ];
  const interpretation: Record<string, string[]> = {};
  for (const attribute of attributesToCheck) {
    interpretation[attribute] = getInterpretation(comparison, attribute);
  }
  const coordSystemMessages = coordinateSystemInterpretation(comparison);

  return (
    <div className='mt-12'>
      <div className='flex justify-between items-center'>
        <h4 className='font-light'>Comparison Results</h4>
        <LinkToLocalComparison comparison={comparison} />
      </div>

      <div className='flex items-end justify-between'>
        <h6 className='font-semibold mt-4'>Selected Collections:</h6>
        <div className='inline'>
          <label className='font-medium inline-block'>Digest A:</label>
          <LinkedCollectionDigest digest={comparison.digests.a} />
        </div>
        <div className='inline'>
          <label className='font-medium inline-block'>Digest B:</label>
          {comparison.digests.b === 'POSTed seqcol' ? (
            <>
              <span className='font-mono text-sm ml-1'>
                POSTed seqcol <Link to='/scom'>(Custom SCOM Input)</Link>
              </span>
            </>
            ) : <LinkedCollectionDigest digest={comparison.digests.b}/>}
        </div>
      </div>

      <h5 className='mt-6'>Interpretation Summary</h5>
      <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
        <div>
          <ReportCard
            title="Sequences"
            tooltipText="This assessment reports on the sequences only, without regard to their names."
            messageArray={interpretation['sequences']}
            colorScheme="info"
          />
        </div>
        <div>
          <ReportCard
            title="Coordinate System"
            tooltipText="This assessment reports on the compatibility of the names and lengths of the sequences, without regard to sequence content."
            messageArray={coordSystemMessages}
            colorScheme="warning"
          />
        </div>
      </div>

      <h5 className='mt-6'>Details</h5>

      <h6 className='font-semibold mt-4'>Attributes:</h6>
      <div className='flex'>
        <label className='kv__term flex justify-end px-6 font-medium'>
          Found in collection A only:
        </label>
        {comparison.attributes.a_only.length > 0 ? (
          comparison.attributes.a_only.join(', ')
        ) : (
          <span>None</span>
        )}
      </div>
      <div className='flex'>
        <label className='kv__term flex justify-end px-6 font-medium'>
          Found in collection B only:
        </label>
        {comparison.attributes.b_only.length > 0 ? (
          comparison.attributes.b_only.join(', ')
        ) : (
          <span>None</span>
        )}
      </div>
      <div className='flex mb-4'>
        <label className='kv__term flex justify-end px-6 font-medium'>
          Found in both:
        </label>
        {comparison.attributes.a_and_b.length > 0 ? (
          comparison.attributes.a_and_b.join(', ')
        ) : (
          <span>None</span>
        )}
      </div>

      <h6 className='font-semibold mt-2'>
        Array Elements{' '}
        <span className='font-normal'>(number of elements found in both)</span>:
      </h6>
      <div className='mb-4'>
        {Object.entries(comparison.array_elements.a_and_b_count).map(
          ([key, value]) => (
            <div className='flex' key={key}>
              <label className='kv__term flex justify-end px-6 font-medium'>
                {key}:
              </label>
              {value}
            </div>
          ),
        )}
      </div>

      <h6 className='font-semibold mt-2'>
        Sequence Order Check{' '}
        <span className='font-normal'>(are the elements in matching order?)</span>
        :
      </h6>
      <div className='mb-4'>
        {Object.entries(comparison.array_elements.a_and_b_same_order).map(
          ([key, value]) => (
            <div className='flex' key={key}>
              <label className='kv__term flex justify-end px-6 font-medium'>
                {key}:
              </label>
              {value === null ? 'null' : String(value)}
            </div>
          ),
        )}
      </div>

      <div className='flex justify-between items-center'>
        <h5 className='mt-6'>Raw View</h5>
        <a
          className='btn btn--secondary btn--sm'
          href={api_url}
          target='_blank'
          rel='noopener noreferrer'
        >
          <Icon name="external" className="mr-2" />
          API
        </a>
      </div>

      <pre className='card card__body bg-surface-muted'>{comp_str}</pre>
    </div>
  );
};

export { ComparisonView };
