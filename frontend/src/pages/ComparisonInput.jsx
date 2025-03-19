// This component will provide a textarea for a user to paste a Comparision,
// Which will then show a ComparisonView component with the parsed comparison
// data.


import React, { useState } from 'react';
import { ComparisonView } from './ComparisonView.jsx';
import { API_BASE } from '../utilities.jsx';


const ComparisonInput = () => {
  const [comparison, setComparison] = useState(null);
  const [comparisonStr, setComparisonStr] = useState('');

  const handleComparisonChange = (event) => {
    setComparisonStr(event.target.value);
  };

  const handleComparisonSubmit = () => {
    const comparison = JSON.parse(comparisonStr);
    setComparison(comparison);
  };

  return (
    <div>
      <h2>Comparison Input</h2>
        <p>Paste the output of `/comparison` here:</p>
      <textarea
        value={comparisonStr}
        onChange={handleComparisonChange}
        className="form-control"
        rows="10"
      ></textarea>
      <button
        onClick={handleComparisonSubmit}
        className="btn btn-primary mt-3"
      >
        Submit
      </button>
      {comparison && <ComparisonView paramComparison={comparison} />}
    </div>
  );
}

export { ComparisonInput };