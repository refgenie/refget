// This component will provide a textarea for a user to paste a Comparision,
// Which will then show a ComparisonView component with the parsed comparison
// data.


import React, { useEffect, useState } from 'react';
import { ComparisonView } from './ComparisonView.jsx';
import { API_BASE } from '../utilities.jsx';
import { useSearchParams } from 'react-router-dom';



const ComparisonInput = () => {
  const [comparison, setComparison] = useState(null);
  const [comparisonStr, setComparisonStr] = useState('');
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
      <h2>SeqCol Comparison Interpretation Module (SCIM)</h2>
        <p>This tool runs a local interpretation of the output of a sequence collection comparison. Paste the output of `/comparison` here:</p>
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
        className="btn btn-primary mt-3 mx-3">Clear</button>

      <hr/>

      {comparison && <ComparisonView paramComparison={comparison} />}
    </div>
  );
}

export { ComparisonInput };