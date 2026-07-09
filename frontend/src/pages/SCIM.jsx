import { useEffect, useState } from 'react';
import { useSearchParams, useLoaderData } from 'react-router-dom';
import toast from 'react-hot-toast';

import { API_BASE, encodeToBase64, decodeFromBase64 } from '../utilities.jsx';
import { ComparisonView } from './ComparisonView.jsx';

// Seqcol Comparison Interpretation Module (SCIM)
// This component will provide a textarea for a user to paste a Comparision,
// Which will then show a ComparisonView component with the parsed comparison
// data.

const SCIM = () => {
  const loaderData = useLoaderData();
  const [comparison, setComparison] = useState(loaderData);
  const [comparisonStr, setComparisonStr] = useState(
    loaderData ? JSON.stringify(loaderData, null, 2) : '',
  );
  const [searchParams] = useSearchParams();

  useEffect(() => {
    window.scrollTo({
      top: 0,
      left: 0,
      behavior: 'auto',
    });
  }, []);

  // get state from query param if it exists
  useEffect(() => {
    const comparisonFromQuery = searchParams.get('val');
    if (comparisonFromQuery) {
      try {
        // decode base64encoded string
        const decodedComparisonFromQuery = decodeFromBase64(comparisonFromQuery);
        // prettify the comparison string
        const prettyComparison = JSON.stringify(
          JSON.parse(decodedComparisonFromQuery),
          null,
          2,
        );
        // Initializing form state from the URL query param is intentional
        // synchronization with an external source.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setComparisonStr(prettyComparison);

        const parsedComparison = JSON.parse(decodedComparisonFromQuery);
        setComparison(parsedComparison);
      } catch {
        toast.error('Invalid comparison URL. The data may be corrupted.');
        setComparison(null);
        setComparisonStr('');
      }
    }
  }, [searchParams]);

  const handleComparisonChange = (event) => {
    setComparisonStr(event.target.value);
  };

  const handleComparisonSubmit = () => {
    let parsedComparison;

    // Parse JSON with error handling
    try {
      parsedComparison = JSON.parse(comparisonStr);
    } catch {
      toast.error(
        <span>
          <strong>Error:</strong> Invalid JSON format. Please check your input.
        </span>,
      );
      return;
    }

    // Validate comparison structure
    if (!parsedComparison?.digests?.a || !parsedComparison?.digests?.b) {
      toast.error(
        <span>
          <strong>Error:</strong> Invalid comparison format. Please check your
          input.
        </span>,
      );
      return;
    }

    // Only set comparison if validation passes
    setComparison(parsedComparison);

    // update the query param to base64 encoded string
    const base64encodedComparison = encodeToBase64(comparisonStr);
    window.history.pushState(
      {},
      '',
      `${window.location.pathname}?val=${base64encodedComparison}`,
    );
  };

  const clearComparison = () => {
    setComparisonStr('');
    setComparison(null);
    window.history.pushState({}, '', `${window.location.pathname}`);
  };

  const loadExample = () => {
    const exampleData =
      'eyJkaWdlc3RzIjp7ImEiOiJYWmxyY0VHaTZtbG9wWjJ1RDhPYkhrUUIxZDBvRHdLayIsImIiOiJRdlQ1dEFRMEI4Vmt4ZC1xRmZ0bHpFazJReWZQdGdPdiJ9LCJhdHRyaWJ1dGVzIjp7ImFfb25seSI6W10sImJfb25seSI6W10sImFfYW5kX2IiOlsibGVuZ3RocyIsIm5hbWVfbGVuZ3RoX3BhaXJzIiwibmFtZXMiLCJzZXF1ZW5jZXMiLCJzb3J0ZWRfc2VxdWVuY2VzIl19LCJhcnJheV9lbGVtZW50cyI6eyJhX2NvdW50Ijp7Imxlbmd0aHMiOjMsIm5hbWVfbGVuZ3RoX3BhaXJzIjozLCJuYW1lcyI6Mywic2VxdWVuY2VzIjozLCJzb3J0ZWRfc2VxdWVuY2VzIjozfSwiYl9jb3VudCI6eyJsZW5ndGhzIjozLCJuYW1lX2xlbmd0aF9wYWlycyI6MywibmFtZXMiOjMsInNlcXVlbmNlcyI6Mywic29ydGVkX3NlcXVlbmNlcyI6M30sImFfYW5kX2JfY291bnQiOnsibGVuZ3RocyI6MywibmFtZV9sZW5ndGhfcGFpcnMiOjAsIm5hbWVzIjowLCJzZXF1ZW5jZXMiOjMsInNvcnRlZF9zZXF1ZW5jZXMiOjN9LCJhX2FuZF9iX3NhbWVfb3JkZXIiOnsibGVuZ3RocyI6dHJ1ZSwibmFtZV9sZW5ndGhfcGFpcnMiOm51bGwsIm5hbWVzIjpudWxsLCJzZXF1ZW5jZXMiOnRydWUsInNvcnRlZF9zZXF1ZW5jZXMiOnRydWV9fX0=';

    const decodedComparison = decodeFromBase64(exampleData);
    const prettyComparison = JSON.stringify(
      JSON.parse(decodedComparison),
      null,
      2,
    );

    setComparisonStr(prettyComparison);
    setComparison(JSON.parse(decodedComparison));

    // Update URL
    window.history.pushState(
      {},
      '',
      `${window.location.pathname}?val=${exampleData}`,
    );
  };

  return (
    <div className='row mb-5'>
      <div className='col-12'>
        <h4 className='fw-light'>
          Seqcol Comparison Interpretation Module (SCIM)
        </h4>
        <p className='mt-3 mb-1 text-muted'>
          This tool visualizes the output of a sequence collection comparison,
          helping you understand how two reference genomes differ.
        </p>

        <div className='alert alert-light border small'>
          <strong>How to get comparison output:</strong>
          <ul className='mb-2 mt-2'>
            <li>
              <strong>Via API:</strong> Call the <code>/comparison/{'{digest1}'}/{'{digest2}'}</code> endpoint
              on any SeqCol API server (e.g., <a href={`${API_BASE}/docs#/Sequence%20collections/compare_2_digests_comparison__digest1___digest2__get`} target="_blank" rel="noopener noreferrer">see API docs</a>)
            </li>
            <li>
              <strong>Via Python:</strong> Use <code>seqcol.compare(digest1, digest2)</code> from the refget package
            </li>
            <li>
              <strong>Quick start:</strong> Use the example button to load example data
            </li>
          </ul>
          <button
            className='btn btn-outline-primary'
            onClick={loadExample}
          >
            <i className='bi bi-play-circle me-2'></i>
            Load Example Data
          </button>
        </div>

        <div className='card mt-4'>
          <div className='card-header tiny d-flex justify-content-between'>
            <span className='fw-bold'>
              Sequence Collection Comparison Output
            </span>
            <button
              className='btn btn-success btn-xs shadow-sm ms-auto'
              onClick={handleComparisonSubmit}
            >
              Submit
            </button>
            <button
              className='btn btn-danger btn-xs shadow-sm ms-1'
              onClick={clearComparison}
            >
              Clear
            </button>
          </div>
          <textarea
            value={comparisonStr}
            onChange={handleComparisonChange}
            placeholder='Paste the output of `/comparison` here.'
            className='form-control tiny border-0 rounded-0 rounded-bottom z-active'
            rows='12'
          />
        </div>
      </div>

      {/* <hr/> */}
      {comparison && <ComparisonView paramComparison={comparison} />}
    </div>
  );
};

export { SCIM };
