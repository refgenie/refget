import { useState } from 'react';
import { LinkedCollectionDigest } from '../components/ValuesAndDigests.jsx';
import { useLoaderData } from 'react-router-dom';

import { API_BASE } from '../utilities.jsx';

const CoordSystemReport = ({ messageArray }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className='card border'>
      <div className='card-header bg-warning bg-opacity-25 border-bottom'>
        <div className='d-flex align-items-center'>
          <span className='fw-medium text-warning-emphasis'>
            Coordinate System
          </span>
          <div className='position-relative'>
            <span
              className='ms-2 text-warning-emphasis'
              style={{
                width: '20px',
                height: '20px',
                fontSize: '0.7rem',
                cursor: 'pointer',
              }}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              <i className='bi bi-question-circle-fill'></i>
            </span>
            {showTooltip && (
              <div
                className='position-absolute bg-dark text-white rounded p-2 shadow-lg'
                style={{
                  left: '25px',
                  top: '0',
                  width: '250px',
                  fontSize: '0.75rem',
                  zIndex: 1050,
                }}
              >
                This assessment reports on the compatibility of the names and
                lengths of the sequences, without regard to sequence content.
              </div>
            )}
          </div>
        </div>
      </div>

      <div className='card-body bg-warning bg-opacity-10'>
        <ul className='mb-0'>
          {messageArray.map((msg, index) => (
            <li key={index}>{msg}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

const SequencesReport = ({ messageArray }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className='card border'>
      <div className='card-header bg-info bg-opacity-25 border-bottom'>
        <div className='d-flex align-items-center'>
          <span className='fw-medium text-info-emphasis'>Sequences</span>
          <div className='position-relative'>
            <span
              className='ms-2 text-info-emphasis'
              style={{
                width: '20px',
                height: '20px',
                fontSize: '0.7rem',
                cursor: 'pointer',
              }}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              <i className='bi bi-question-circle-fill'></i>
            </span>
            {showTooltip && (
              <div
                className='position-absolute bg-dark text-white rounded p-2 shadow-lg'
                style={{
                  left: '25px',
                  top: '0',
                  width: '250px',
                  fontSize: '0.75rem',
                  zIndex: 1050,
                }}
              >
                This assessment reports on the sequences only, without regard to
                their names.
              </div>
            )}
          </div>
        </div>
      </div>

      <div className='card-body bg-info bg-opacity-10'>
        <ul className='mb-0'>
          {messageArray.map((msg, index) => (
            <li key={index}>{msg}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// Component to display the comparison between two collections
// ✅❔❌❔
const coordinateSystemInterpretation = (comparison) => {
  const lengthsANotB =
    comparison.array_elements.a.lengths -
    comparison.array_elements.a_and_b.lengths;
  const lengthsBNotA =
    comparison.array_elements.b.lengths -
    comparison.array_elements.a_and_b.lengths;
  const namesANotB =
    comparison.array_elements.a.names - comparison.array_elements.a_and_b.names;
  const namesBNotA =
    comparison.array_elements.b.names - comparison.array_elements.a_and_b.names;
  const nlpANotB =
    comparison.array_elements.a.name_length_pairs -
    comparison.array_elements.a_and_b.name_length_pairs;
  const nlpBNotA =
    comparison.array_elements.b.name_length_pairs -
    comparison.array_elements.a_and_b.name_length_pairs;
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
  } else if (comparison.array_elements.a_and_b.name_length_pairs !== 0) {
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

const LinkToLocalComparison = ({ comparison }) => {
  const [copied, setCopied] = useState(false);
  const base64encodedComparison = btoa(JSON.stringify(comparison));
  return (
    <button
      className='btn btn-secondary btn-sm'
      onClick={() => {
        navigator.clipboard.writeText(
          `${window.location.origin}/scim?val=${base64encodedComparison}`,
        );
        setCopied(true);
        setTimeout(() => {
          setCopied(false);
        }, 2000);
        s;
      }}
    >
      {copied ? (
        <>
          <i className='bi bi-check me-2' />
          Copied!
        </>
      ) : (
        <>
          <i className='bi bi-clipboard-fill me-2' />
          Result URL
        </>
      )}
    </button>
  );
};

const ComparisonView = ({ paramComparison }) => {
  const loaderData = useLoaderData();
  const comparison = paramComparison || loaderData;
  console.log('ComparisonView', comparison);
  const comp_str = JSON.stringify(comparison, null, 2);

  let api_url = `${API_BASE}/comparison/${comparison.digests.a}/${comparison.digests.b}`;

  // Do some analysis for interpretation

  // ✅❔❌
  const getInterpretation = (comparison, attribute) => {
    const nSequencesA = comparison.array_elements.a[attribute];
    const nSequencesB = comparison.array_elements.b[attribute];
    const aNotB =
      comparison.array_elements.a[attribute] -
      comparison.array_elements.a_and_b[attribute];
    const bNotA =
      comparison.array_elements.b[attribute] -
      comparison.array_elements.a_and_b[attribute];
    const orderCheck = comparison.array_elements.a_and_b_same_order[attribute];

    let interpTerm = '';
    const msgArray = [];

    if (
      comparison.array_elements.a_and_b[attribute] == nSequencesA &&
      comparison.array_elements.a_and_b[attribute] == nSequencesB
    ) {
      msgArray.push(`🟰 The ${attribute} contents are identical.`);
      if (orderCheck === true) {
        msgArray.push('✅ The elements are in the same order.');
      } else if (orderCheck === false) {
        msgArray.push('❌ The elements are in different order.');
      }
      interpTerm = 'identical_content';
    }
    if (
      comparison.array_elements.a_and_b[attribute] == nSequencesA &&
      comparison.array_elements.a_and_b[attribute] < nSequencesB
    ) {
      msgArray.push(
        `Collection B contains all ${nSequencesA} ${attribute} from collection A, and ${bNotA} additional.`,
      );
      interpTerm = 'subset';
    }
    if (
      comparison.array_elements.a_and_b[attribute] == nSequencesB &&
      comparison.array_elements.a_and_b[attribute] < nSequencesA
    ) {
      msgArray.push(
        `Collection A contains all ${nSequencesB} ${attribute} from collection B, and ${aNotB} additional.`,
      );
      interpTerm = 'subset';
    }
    if (comparison.array_elements.a_and_b[attribute] === 0) {
      msgArray.push(`The collections' ${attribute} contents are disjoint.`);
      interpTerm = 'disjoint';
    } else if (
      comparison.array_elements.a_and_b[attribute] < nSequencesA &&
      comparison.array_elements.a_and_b[attribute] < nSequencesB
    ) {
      msgArray.push(
        `The collections' ${attribute} contents are partially overlapping; some are shared, and some are unique to each collection.`,
      );
      interpTerm = 'partial_overlap';
    }

    return msgArray;
  };

  const attributesToCheck = [
    'sequences',
    'names',
    'lengths',
    'name_length_pairs',
  ];
  const interpretation = {};
  for (let attribute of attributesToCheck) {
    interpretation[attribute] = getInterpretation(comparison, attribute);
  }
  // console.log(interpretation)
  console.log('Comparison:', comparison);
  const coordSystemMessages = coordinateSystemInterpretation(comparison);

  return (
    <div className='mt-5'>
      <div className='d-flex justify-content-between align-items-center'>
        <h4 className='fw-light'>Comparison Results</h4>
        <LinkToLocalComparison comparison={comparison} />
      </div>

      <div className='d-flex align-items-end justify-content-between home'>
        <h6 className='fw-semibold mt-3'>Selected Collections:</h6>
        <div className='d-inline'>
          <label className='fw-medium d-inline-block'>Digest A:</label>
          <LinkedCollectionDigest digest={comparison.digests.a} />
        </div>
        <div className='d-inline'>
          <label className='fw-medium d-inline-block'>Digest B:</label>
          <LinkedCollectionDigest digest={comparison.digests.b} />
        </div>
      </div>

      <h5 className='mt-4'>Interpretation Summary</h5>
      <div className='row'>
        <div className='col-md-6'>
          <SequencesReport messageArray={interpretation['sequences']} />
        </div>
        <div className='col-md-6'>
          <CoordSystemReport messageArray={coordSystemMessages} />
        </div>
      </div>

      <h5 className='mt-4'>Details</h5>

      <h6 className='fw-semibold mt-3'>Attributes:</h6>
      <div className='d-flex'>
        <label className='col-sm-3 d-flex justify-content-end px-4 fw-medium'>
          Found in collection A only:
        </label>
        {comparison.attributes.a_only != '' ? (
          comparison.attributes.a_only.join(', ')
        ) : (
          <span className=''>None</span>
        )}
      </div>
      <div className='d-flex'>
        <label className='col-sm-3 d-flex justify-content-end px-4 fw-medium'>
          Found in collection B only:
        </label>
        {comparison.attributes.b_only != '' ? (
          comparison.attributes.b_only.join(', ')
        ) : (
          <span className=''>None</span>
        )}
      </div>
      <div className='d-flex mb-3'>
        <label className='col-sm-3 d-flex justify-content-end px-4 fw-medium'>
          Found in both:
        </label>
        {comparison.attributes.a_and_b != '' ? (
          comparison.attributes.a_and_b.join(', ')
        ) : (
          <span className=''>None</span>
        )}
      </div>

      <h6 className='fw-semibold mt-2'>
        Array Elements{' '}
        <span className='fw-normal'>(number of elements found in both)</span>:
      </h6>
      <div className='row mb-3'>
        {Object.entries(comparison.array_elements.a_and_b).map(
          ([key, value]) => (
            <div className='d-flex' key={key}>
              <label className='col-sm-3 d-flex justify-content-end px-4 fw-medium'>
                {key}:
              </label>
              {value}
            </div>
          ),
        )}
      </div>

      <h6 className='fw-semibold mt-2'>
        Sequence Order Check{' '}
        <span className='fw-normal'>(are the elements in matching order?)</span>
        :
      </h6>
      <div className='row mb-3'>
        {Object.entries(comparison.array_elements.a_and_b_same_order).map(
          ([key, value]) => (
            <div className='d-flex' key={key}>
              <label className='col-sm-3 d-flex justify-content-end px-4 fw-medium'>
                {key}:
              </label>
              {value !== null ? value.toString() : 'null'}
            </div>
          ),
        )}
      </div>

      <div className='d-flex justify-content-between align-items-center'>
        <h5 className='mt-4'>Raw View</h5>
        <a
          className='btn btn-secondary btn-sm'
          href={api_url}
          target='_blank'
          rel='noopener noreferrer'
        >
          <i className='bi bi-box-arrow-up-right me-2' />
          API
        </a>
      </div>

      <pre className='card card-body bg-light'>{comp_str}</pre>
    </div>
  );
};

export { ComparisonView };
