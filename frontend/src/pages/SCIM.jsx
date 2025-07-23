import React, { useEffect, useState } from 'react';
import { ComparisonView } from './ComparisonView.jsx';
import { API_BASE } from '../utilities.jsx';
import { useSearchParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useLoaderData } from "react-router-dom"

// Seqcol Comparison Interpretation Module (SCIM)
// This component will provide a textarea for a user to paste a Comparision,
// Which will then show a ComparisonView component with the parsed comparison
// data.

const SCIM = () => {
  const loaderData = useLoaderData()
  const [comparison, setComparison] = useState(loaderData);
  const [comparisonStr, setComparisonStr] = useState(loaderData ? JSON.stringify(loaderData, null, 2) : '');
  const [searchParams] = useSearchParams();

  // get state from query param if it exists
  useEffect(() => {
    const comparisonFromQuery = searchParams.get('val');
    if (comparisonFromQuery) {
      console.log('Encoded comparison from query param:', comparisonFromQuery);
      // decode base64encoded string
      const decodedComparisonFromQuery = atob(comparisonFromQuery);
      // prettify the comparison string
      const prettyComparison = JSON.stringify(JSON.parse(decodedComparisonFromQuery), null, 2);
      console.log('Decoded comparison from query:', prettyComparison)
      setComparisonStr(prettyComparison);

      const parsedComparison = JSON.parse(decodedComparisonFromQuery);
      setComparison(parsedComparison);
    }
  }, [searchParams]);

  const handleComparisonChange = (event) => {
    setComparisonStr(event.target.value);
  };

  const handleComparisonSubmit = () => {
    const comparison = JSON.parse(comparisonStr);
    setComparison(comparison);
    // update the query param to base64 encoded string
    const base64encodedComparison = btoa(comparisonStr);
    window.history.pushState({}, '', `${window.location.pathname}?val=${base64encodedComparison}`);
  };

  const clearComparison = () => {
    console.log("Clearing comparison");
    setComparisonStr('');
    setComparison(null);
    window.history.pushState({}, '', `${window.location.pathname}`);
  };

  return (
    <div>
      <h4 className='fw-light'>Seqcol Comparison Interpretation Module (SCIM)</h4>
        <p className='mt-3 mb-1'>This tool runs a local interpretation of the output of a sequence collection comparison. Paste the output of `/comparison` here:</p>
      <textarea
        value={comparisonStr}
        onChange={handleComparisonChange}
        className="form-control"
        rows="10"
      ></textarea>
      <button
        onClick={handleComparisonSubmit}
        className="btn btn-primary mt-3"
      > Submit </button>

      <button onClick={clearComparison} 
        className="btn btn-primary mt-3 mx-2">Clear</button>

      <Link 
        to={`/scim?val=eyJkaWdlc3RzIjp7ImEiOiJYWmxyY0VHaTZtbG9wWjJ1RDhPYkhrUUIxZDBvRHdLayIsImIiOiJRdlQ1dEFRMEI4Vmt4ZC1xRmZ0bHpFazJReWZQdGdPdiJ9LCJhdHRyaWJ1dGVzIjp7ImFfb25seSI6W10sImJfb25seSI6W10sImFfYW5kX2IiOlsibGVuZ3RocyIsIm5hbWVfbGVuZ3RoX3BhaXJzIiwibmFtZXMiLCJzZXF1ZW5jZXMiLCJzb3J0ZWRfc2VxdWVuY2VzIl19LCJhcnJheV9lbGVtZW50cyI6eyJhIjp7Imxlbmd0aHMiOjMsIm5hbWVfbGVuZ3RoX3BhaXJzIjozLCJuYW1lcyI6Mywic2VxdWVuY2VzIjozLCJzb3J0ZWRfc2VxdWVuY2VzIjozfSwiYiI6eyJsZW5ndGhzIjozLCJuYW1lX2xlbmd0aF9wYWlycyI6MywibmFtZXMiOjMsInNlcXVlbmNlcyI6Mywic29ydGVkX3NlcXVlbmNlcyI6M30sImFfYW5kX2IiOnsibGVuZ3RocyI6MywibmFtZV9sZW5ndGhfcGFpcnMiOjAsIm5hbWVzIjowLCJzZXF1ZW5jZXMiOjMsInNvcnRlZF9zZXF1ZW5jZXMiOjN9LCJhX2FuZF9iX3NhbWVfb3JkZXIiOnsibGVuZ3RocyI6dHJ1ZSwibmFtZV9sZW5ndGhfcGFpcnMiOm51bGwsIm5hbWVzIjpudWxsLCJzZXF1ZW5jZXMiOnRydWUsInNvcnRlZF9zZXF1ZW5jZXMiOnRydWV9fX0=`}
        className="btn btn-primary mt-3">
        Load Example
      </Link>
      {/* <hr/> */}
      {comparison && <ComparisonView paramComparison={comparison} />}
    </div>
  );
}

export { SCIM };