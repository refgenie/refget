import React, { useEffect, useState } from 'react';
import { API_BASE } from '../utilities.jsx';
import { useLoaderData } from 'react-router-dom'
import toast from 'react-hot-toast';


import { fetchSimilarities, fetchSimilaritiesJSON } from '../services/fetchData.jsx'
import { HeatmapPlot } from '../components/HeatmapPlot.jsx'
import { ScatterPlot } from '../components/ScatterPlot.jsx'
import { NetworkGraph } from '../components/NetworkGraph.jsx';


const Similarities = () => {
  const loaderData = useLoaderData()
  const collections = loaderData[0]

  const [selectedCollectionsIndex, setSelectedCollectionsIndex] = useState(new Array(collections.results.length).fill(true));
  const [customCollections, setCustomCollections] = useState([]);
  const allCollections = [...collections.results, ...customCollections.map(c => c.selectedDigest)];

  const [customCollectionName, setCustomCollectionName] = useState('');
  const [customCollectionJSON, setCustomCollectionJSON] = useState('');
  const [similarities, setSimilarities] = useState(null);
  const [heatmapMetric, setHeatmapMetric] = useState('sequences');
  const [networkMetric, setNetworkMetric] = useState('sequences');
  const [networkThreshold, setNetworkThreshold] = useState(0.50);
  const [customCount, setCustomCount] = useState(1);

  const selectedCollections = allCollections.filter((_, index) => selectedCollectionsIndex[index])

  const handleSelectCollection = (index) => {
    setSelectedCollectionsIndex(prev => {
      const newArray = [...prev];
      newArray[index] = !newArray[index];
      return newArray;
    })
  }

  const handleAddCustomCollection = async (data, name) => {
    try {
      data = JSON.parse(data);
    } catch (e) {
      toast.error(
        <span>
          <strong>Error:</strong> Invalid JSON format. Please check your input.
        </span>
      )
      return;
    }

    if (allCollections.includes(name)) {
      toast.error(
        <span>
          <strong>Error:</strong> Collection with name already exists. Please try another name.
        </span>
      );
      return;
    }

    try {
      const result = await fetchSimilaritiesJSON(data);
      if (result?.similarities) {

        const customDigest = 'custom' + (customCount)

        const flattenedSimilarities = result.similarities.map(s => ({
          selectedDigest: name !== '' ? name : customDigest,
          comparedDigest: s.digest,
          lengths: s.similarities.lengths,
          name_length_pairs: s.similarities.name_length_pairs,
          names: s.similarities.names,
          sequences: s.similarities.sequences,
          sorted_sequences: s.similarities.sorted_sequences,
          custom: true
        }));

        setCustomCollections(prev => [...prev, { selectedDigest: name !== '' ? name : customDigest, similarities: flattenedSimilarities }]);
        setSelectedCollectionsIndex(prev => [...prev, true]);
        setCustomCount(prev => prev + 1);

        toast.success('Collection added to list.')
      }
    } catch (e) {
      toast.error(
        <span>
          <strong>Error:</strong> Collection is invalid. Please check your input.
        </span>
      );
      return;
    }
  };

  useEffect(() => {
    const fetchAllSimilarities = async () => {
      const allSimilarities = [];

      for (let i = 0; i < selectedCollectionsIndex.length; i++) {
        if (!selectedCollectionsIndex[i]) continue;

        const collection = allCollections[i];
        
        if (i < collections.results.length) { // server collection
          try {
            const result = await fetchSimilarities(collection);
            if (result?.similarities) {
              const flattenedSimilarities = result.similarities.map(s => ({
                selectedDigest: collection,
                comparedDigest: s.digest,
                lengths: s.similarities.lengths,
                name_length_pairs: s.similarities.name_length_pairs,
                names: s.similarities.names,
                sequences: s.similarities.sequences,
                sorted_sequences: s.similarities.sorted_sequences,
                custom: false
              }));
              allSimilarities.push(...flattenedSimilarities);
            }
          } catch (error) {
            console.error(`Error fetching similarities for ${collection}:`, error);
          }
        } else { // custom collection
          const customIndex = i - collections.results.length;
          const customCollection = customCollections[customIndex];
          if (customCollection) {
            allSimilarities.push(...customCollection.similarities);
          }
        }
      }

      setSimilarities(allSimilarities.length > 0 ? allSimilarities : null);
    };

    fetchAllSimilarities();
  }, [selectedCollectionsIndex, customCollections]);

  return (
    <>
      <div className='row mb-2'>
        <div className='col-12'>

          <h4 className='fw-light'>Seqcol Similarity Metrics</h4>
          <p className='mt-3 mb-2'>This tool provides metrics and visuals for comparisons between sequence collections on the server, or with one of your choice. Browse sequence collections to compare below.</p>
        
          <div className='row'>
            <div className='col-6'>
              <div className='card'>
                <div className='card-header tiny d-flex justify-content-between'>
                  <span className='fw-bold'>Selected Sequence Collections</span>
                  <span>({selectedCollections.length} selected)</span>
                </div>
                <ul className='list-group list-group-flush overflow-auto' style={{maxHeight: '200px'}}>
                  {allCollections && (
                    allCollections.map((collection, index) => 
                      <li className='list-group-item pb-0 tiny' key={index}>
                        <div className='d-flex align-items-between'>
                          <div className='form-check form-switch'>
                            <input 
                              className='form-check-input cursor-pointer me-3' 
                              type='checkbox' 
                              id={'collection_' + index} 
                              onChange={() => handleSelectCollection(index)} 
                              checked={selectedCollectionsIndex[index]}
                            />
                            <label className='form-check-label cursor-pointer' htmlFor={'collection_' + index}>
                              {collection}
                            </label>
                          </div>
                          {index >= collections.results.length && (
                            <span 
                              className='ms-auto bi bi-trash-fill text-danger cursor-pointer' 
                              onClick={() => {
                                const customIndex = index - collections.results.length;
                                setCustomCollections(prev => prev.filter((_, i) => i !== customIndex));
                                setSelectedCollectionsIndex(prev => prev.filter((_, i) => i !== index));
                                toast.success('Custom collection removed.')
                              }}
                            />
                          )}
                        </div>
                      </li>
                    )
                  )}
                </ul>
              </div>
            </div>
              
            <div className='col-6'>
              <div className='card'>
                <div className='card-header tiny d-flex justify-content-between'>
                  <span className='fw-bold'>Add Custom Collection</span>
                  <button className='btn btn-success btn-xs shadow-sm' onClick={async () => handleAddCustomCollection(customCollectionJSON, customCollectionName)}>Add</button>
                </div>
                <input 
                  id='custom-collection-name'
                  type='text'
                  onChange={(e) => setCustomCollectionName(e.target.value)}
                  placeholder='Name or digest of custom collection (optional)'
                  className='form-control tiny border-0 rounded-0 border-bottom z-active'
                />
                <textarea
                  id='custom-collection-json'
                  onChange={(e) => setCustomCollectionJSON(e.target.value)}
                  placeholder='If you have a custom sequence collection, enter the output of `refget digest-fasta "yourfasta.fa" -l 2` here'
                  className='form-control tiny border-0 rounded-0 rounded-bottom z-active'
                  style={{maxHeight: 'calc(200px - 32.333333px)'}}
                  rows='12'
                />
              </div>
              
            </div>
          </div>
        </div>
      </div>          

      {similarities ? (
        <div className='row'>
          <div className='col-12'>

            <div className='d-flex align-items-end justify-content-between mt-4 mb-2'>
              <h5 className='fw-light'>Heatmap</h5>
              <select className='form-select form-select-sm w-25' aria-label='heatmap-select' value={heatmapMetric} onChange={e => setHeatmapMetric(e.target.value)}>
                <option value='lengths'>Lengths</option>
                <option value='name_length_pairs'>Name Length Pairs</option>
                <option value='names'>Names</option>
                <option value='sequences'>Sequences</option>
                <option value='sorted_sequences'>Sorted Sequences</option>
              </select>
            </div>
            <HeatmapPlot similarities={similarities} metric={heatmapMetric} />

            {/* <h5 className='fw-light mt-4'>Scatterplot</h5>
            <ScatterPlot similarities={similarities} /> */}

            <div className='d-flex align-items-end justify-content-between mt-5 mb-2'>
              <h5 className='fw-light'>Network Graph</h5>
              <div className='input-group input-group-sm ms-auto w-25'>
                <span className='input-group-text'>Threshold</span>
                <input 
                  type='range'
                  min='0'
                  max='1'
                  step='0.01'
                  value={networkThreshold}
                  onChange={e => setNetworkThreshold(Number(e.target.value))}
                  className='form-control form-range'
                  style={{height: 'inherit'}}
                />
                <input 
                  type='number'
                  min='0'
                  max='1'
                  step='0.01'
                  value={networkThreshold}
                  onChange={e => setNetworkThreshold(Number(e.target.value))}
                  className='form-control'
                  style={{maxWidth: '70px'}}
                />
              </div>
              <select className='form-select form-select-sm w-25 ms-2' aria-label='network-select' value={networkMetric} onChange={e => setNetworkMetric(e.target.value)}>
                <option value='lengths'>Lengths</option>
                <option value='name_length_pairs'>Name Length Pairs</option>
                <option value='names'>Names</option>
                <option value='sequences'>Sequences</option>
                <option value='sorted_sequences'>Sorted Sequences</option>
              </select>
            </div>
            <NetworkGraph similarities={similarities} metric={networkMetric} threshold={networkThreshold}/>
            
            <h5 className='fw-light mt-5'>Summary Table</h5>
            <div className='rounded shadow-sm border tiny overflow-x-auto'>
              <table className='table table-striped table-hover table-rounded'>
                <thead>
                  <tr>
                    <th>Selected Digest</th>
                    <th>Compared Digest</th>
                    <th>Lengths</th>
                    <th>Name Length Pairs</th>
                    <th>Names</th>
                    <th>Sequences</th>
                    <th>Sorted Sequences</th>
                  </tr>
                </thead>
                <tbody>
                  {similarities?.map((row, index) => (
                    <tr key={index} className='cursor-pointer'>
                      <td>{row.comparedDigest}</td>
                      <td>{row.selectedDigest}</td>
                      <td>{row.lengths}</td>
                      <td>{row.name_length_pairs}</td>
                      <td>{row.names}</td>
                      <td>{row.sequences}</td>
                      <td>{row.sorted_sequences}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

          </div>
        </div>
      ) : (
        <p className='mt-4'>Loading...</p>
      )}
    </>
  );
}

export { Similarities };
