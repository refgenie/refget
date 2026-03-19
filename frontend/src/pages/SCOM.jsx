import { useCallback, useEffect, useState } from 'react';
import { encodeComparison } from '../utilities.jsx';
import { useLoaderData, useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';

import {
  fetchSimilarities,
  fetchSimilaritiesJSON,
  fetchComparison,
  fetchComparisonJSON,
} from '../services/fetchData.jsx';
import { MultiMetricHeatmapPlot } from '../components/MultiMetricHeatmapPlot.jsx';
import { StripPlot } from '../components/StripPlot.jsx';

import { useSimilaritiesStore } from '../stores/similarities';


const SCOM = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const loaderData = useLoaderData();
  const collections = Array.isArray(loaderData) && loaderData.length >= 1 ? loaderData[0] : null;

  const {
    selectedCollectionsIndex,
    setSelectedCollectionsIndex,
    customCollections,
    setCustomCollections,
    customCollectionName,
    setCustomCollectionName,
    customCollectionJSON,
    setCustomCollectionJSON,
    customCount,
    setCustomCount,
    similarities,
    setSimilarities,
    getAllCollections,
    initializeSelectedCollections,
    sortBy,
    sortAscending,
    sortByColumn,
    resetSort,
    species,
    setSpecies,
    error: storeError,
    setError: setStoreError,
  } = useSimilaritiesStore();

  const [stripJitter, setStripJitter] = useState('none');
  const [stripOrientation, setStripOrientation] = useState('horizontal');
  const [relationship, setRelationship] = useState('oneToMany');
  const [isLoading, setIsLoading] = useState(false);
  const [pendingPrefill, setPendingPrefill] = useState(null);

  const allCollections = getAllCollections(collections);

  useEffect(() => {
    initializeSelectedCollections(collections);
  }, [collections, initializeSelectedCollections]);

  // Handle prefill from digest page - load data
  useEffect(() => {
    if (searchParams.get('prefill') === 'true' && !pendingPrefill) {
      const prefillData = localStorage.getItem('scom-prefill');
      if (prefillData) {
        try {
          const { json, name } = JSON.parse(prefillData);
          setCustomCollectionJSON(JSON.stringify(json, null, 2));
          setCustomCollectionName(name || '');
          localStorage.removeItem('scom-prefill');
          setPendingPrefill({ json, name });
        } catch (e) {
          console.error('Failed to load prefill data:', e);
        }
      }
    }
  }, [searchParams]);

  const selectedCollections = allCollections.filter(
    (_, index) => selectedCollectionsIndex[index],
  );

  const sampleJSON = {
    "lengths": [249250621, 243199373, 198022430, 191154276, 180915260, 171115067, 159138663, 146364022, 141213431, 135534747, 135006516, 133851895, 115169878, 107349540, 102531392, 90354753, 81195210, 78077248, 59128983, 63025520, 48129895, 51304566, 155270560, 59373566, 16569],
    "names": [
      "1",
      "2",
      "3",
      "4",
      "5",
      "6",
      "7",
      "8",
      "9",
      "10",
      "11",
      "12",
      "13",
      "14",
      "15",
      "16",
      "17",
      "18",
      "19",
      "20",
      "21",
      "22",
      "X",
      "Y",
      "MT"
    ],
    "sequences": [
      "SQ.S_KjnFVz-FE7M0W6yoaUDgYxLPc1jyWU",
      "SQ.9KdcA9ZpY1Cpvxvg8bMSLYDUpsX6GDLO",
      "SQ.VNBualIltAyi2AI_uXcKU7M9XUOuA7MS",
      "SQ.iy7Zfceb5_VGtTQzJ-v5JpPbpeifHD_V",
      "SQ.vbjOdMfHJvTjK_nqvFvpaSKhZillW0SX",
      "SQ.KqaUhJMW3CDjhoVtBetdEKT1n6hM-7Ek",
      "SQ.IW78mgV5Cqf6M24hy52hPjyyo5tCCd86",
      "SQ.tTm7wmhz0G4lpt8wPspcNkAD_qiminj6",
      "SQ.HBckYGQ4wYG9APHLpjoQ9UUe9v7NxExt",
      "SQ.-BOZ8Esn8J88qDwNiSEwUr5425UXdiGX",
      "SQ.XXi2_O1ly-CCOi3HP5TypAw7LtC6niFG",
      "SQ.105bBysLoDFQHhajooTAUyUkNiZ8LJEH",
      "SQ.Ewb9qlgTqN6e_XQiRVYpoUfZJHXeiUfH",
      "SQ.5Ji6FGEKfejK1U6BMScqrdKJK8GqmIGf",
      "SQ.zIMZb3Ft7RdWa5XYq0PxIlezLY2ccCgt",
      "SQ.W6wLoIFOn4G7cjopxPxYNk2lcEqhLQFb",
      "SQ.AjWXsI7AkTK35XW9pgd3UbjpC3MAevlz",
      "SQ.BTj4BDaaHYoPhD3oY2GdwC_l0uqZ92UD",
      "SQ.ItRDD47aMoioDCNW_occY5fWKZBKlxCX",
      "SQ.iy_UbUrvECxFRX5LPTH_KPojdlT7BKsf",
      "SQ.LpTaNW-hwuY_yARP0rtarCnpCQLkgVCg",
      "SQ.XOgHwwR3Upfp5sZYk6ZKzvV25a4RBVu8",
      "SQ.v7noePfnNpK8ghYXEqZ9NukMXW7YeNsm",
      "SQ.fbS5kAwZUB5-1xVpa7xZ4s_lyDpLPVUo",
      "SQ.k3grVkjY-hoWcCUojHw6VU6GE3MZ8Sct"
    ],
    "sorted_sequences": [
      "SQ.-BOZ8Esn8J88qDwNiSEwUr5425UXdiGX",
      "SQ.105bBysLoDFQHhajooTAUyUkNiZ8LJEH",
      "SQ.5Ji6FGEKfejK1U6BMScqrdKJK8GqmIGf",
      "SQ.9KdcA9ZpY1Cpvxvg8bMSLYDUpsX6GDLO",
      "SQ.AjWXsI7AkTK35XW9pgd3UbjpC3MAevlz",
      "SQ.BTj4BDaaHYoPhD3oY2GdwC_l0uqZ92UD",
      "SQ.Ewb9qlgTqN6e_XQiRVYpoUfZJHXeiUfH",
      "SQ.HBckYGQ4wYG9APHLpjoQ9UUe9v7NxExt",
      "SQ.IW78mgV5Cqf6M24hy52hPjyyo5tCCd86",
      "SQ.ItRDD47aMoioDCNW_occY5fWKZBKlxCX",
      "SQ.KqaUhJMW3CDjhoVtBetdEKT1n6hM-7Ek",
      "SQ.LpTaNW-hwuY_yARP0rtarCnpCQLkgVCg",
      "SQ.S_KjnFVz-FE7M0W6yoaUDgYxLPc1jyWU",
      "SQ.VNBualIltAyi2AI_uXcKU7M9XUOuA7MS",
      "SQ.W6wLoIFOn4G7cjopxPxYNk2lcEqhLQFb",
      "SQ.XOgHwwR3Upfp5sZYk6ZKzvV25a4RBVu8",
      "SQ.XXi2_O1ly-CCOi3HP5TypAw7LtC6niFG",
      "SQ.fbS5kAwZUB5-1xVpa7xZ4s_lyDpLPVUo",
      "SQ.iy7Zfceb5_VGtTQzJ-v5JpPbpeifHD_V",
      "SQ.iy_UbUrvECxFRX5LPTH_KPojdlT7BKsf",
      "SQ.k3grVkjY-hoWcCUojHw6VU6GE3MZ8Sct",
      "SQ.tTm7wmhz0G4lpt8wPspcNkAD_qiminj6",
      "SQ.v7noePfnNpK8ghYXEqZ9NukMXW7YeNsm",
      "SQ.vbjOdMfHJvTjK_nqvFvpaSKhZillW0SX",
      "SQ.zIMZb3Ft7RdWa5XYq0PxIlezLY2ccCgt"
    ],
    "name_length_pairs": [
      {
        "length": 249250621,
        "name": "1"
      },
      {
        "length": 243199373,
        "name": "2"
      },
      {
        "length": 198022430,
        "name": "3"
      },
      {
        "length": 191154276,
        "name": "4"
      },
      {
        "length": 180915260,
        "name": "5"
      },
      {
        "length": 171115067,
        "name": "6"
      },
      {
        "length": 159138663,
        "name": "7"
      },
      {
        "length": 146364022,
        "name": "8"
      },
      {
        "length": 141213431,
        "name": "9"
      },
      {
        "length": 135534747,
        "name": "10"
      },
      {
        "length": 135006516,
        "name": "11"
      },
      {
        "length": 133851895,
        "name": "12"
      },
      {
        "length": 115169878,
        "name": "13"
      },
      {
        "length": 107349540,
        "name": "14"
      },
      {
        "length": 102531392,
        "name": "15"
      },
      {
        "length": 90354753,
        "name": "16"
      },
      {
        "length": 81195210,
        "name": "17"
      },
      {
        "length": 78077248,
        "name": "18"
      },
      {
        "length": 59128983,
        "name": "19"
      },
      {
        "length": 63025520,
        "name": "20"
      },
      {
        "length": 48129895,
        "name": "21"
      },
      {
        "length": 51304566,
        "name": "22"
      },
      {
        "length": 155270560,
        "name": "X"
      },
      {
        "length": 59373566,
        "name": "Y"
      },
      {
        "length": 16569,
        "name": "MT"
      }
    ]
  }

  const handleNavigateSCIM = async (similarityRow) => {
    setStoreError(null);
    try {
      let comparison;
      if (similarityRow.custom) {
        comparison = await fetchComparisonJSON(
          similarityRow.raw,
          similarityRow.comparedDigest,
        );
      } else {
        comparison = await fetchComparison(
          similarityRow.selectedDigest,
          similarityRow.comparedDigest,
        );
      }
      const encodedComparison = encodeComparison(comparison);
      navigate(`/scim?val=${encodedComparison}`);
    } catch (error) {
      setStoreError('Comparison could not be made.');
      toast.error(
        <span>
          <strong>Error:</strong> Comparison could not be made.
        </span>,
      );
    }
  };

  const handleAddCustomCollection = useCallback(async (data, name) => {
    setStoreError(null);
    try {
      data = JSON.parse(data);
    } catch (e) {
      setStoreError('Invalid JSON format. Please check your input.');
      toast.error(
        <span>
          <strong>Error:</strong> Invalid JSON format. Please check your input.
        </span>,
      );
      return;
    }

    try {
      setIsLoading(true);
      const result = await fetchSimilaritiesJSON(data, species);
      if (result?.similarities) {
        const customDigest = 'Input Seqcol';
        const flattenedSimilarities = result.similarities.flatMap((s) => {
          const names = s.human_readable_names.length > 0
            ? s.human_readable_names
            : [s.digest];
          return names.map((humanReadableName) => ({
            selectedDigest: name !== '' ? name : customDigest,
            comparedDigest: s.digest,
            comparedAlias: humanReadableName || s.digest,
            lengths: s.similarities.lengths,
            name_length_pairs: s.similarities.name_length_pairs,
            names: s.similarities.names,
            sequences: s.similarities.sequences,
            sorted_sequences: s.similarities.sorted_sequences,
            custom: true,
            raw: data,
          }));
        });

        if (relationship === 'oneToMany') {
          setCustomCollections([
            {
              selectedDigest: name !== '' ? name : customDigest,
              similarities: flattenedSimilarities,
            },
          ]);
          const serverCollectionCount = collections?.results?.length || 0;
          setSelectedCollectionsIndex((prev) => [
            ...prev.slice(0, serverCollectionCount),
            true,
          ]);
        } else {
          // Add to existing custom collections
          setCustomCollections((prev) => [
            ...prev,
            {
              selectedDigest: name !== '' ? name : customDigest,
              similarities: flattenedSimilarities,
            },
          ]);
          setSelectedCollectionsIndex((prev) => [...prev, true]);
        }
        setCustomCount((prev) => prev + 1);
        toast.success('Input processed.');
      }
    } catch (e) {
      console.error('SCOM submission error:', e);
      console.log('Data that was submitted:', data);
      setStoreError('Collection is invalid. Please check your input.');
      toast.error(
        <span>
          <strong>Error:</strong> Collection is invalid. Please check your
          input.
        </span>,
      );
      return;
    } finally {
      resetSort();
      setIsLoading(false);
    }
  }, [species, relationship, collections, customCollections, customCount, setCustomCollections, setSelectedCollectionsIndex, setCustomCount, resetSort, setIsLoading, setStoreError]);

  // Auto-submit prefilled data (wait for collections to be ready)
  useEffect(() => {
    if (pendingPrefill && !isLoading && collections?.results) {
      handleAddCustomCollection(JSON.stringify(pendingPrefill.json), pendingPrefill.name || '');
      setPendingPrefill(null);
    }
  }, [pendingPrefill, isLoading, collections, handleAddCustomCollection]);

  useEffect(() => {
    const fetchAllSimilarities = async () => {
      const allSimilarities = [];

      for (let i = 0; i < selectedCollectionsIndex.length; i++) {
        if (!selectedCollectionsIndex[i]) continue;

        const customIndex = i - collections.results.length;
        const customCollection = customCollections[customIndex];
        if (customCollection) {
          allSimilarities.push(...customCollection.similarities);
        }
      }

      setSimilarities(allSimilarities.length > 0 ? allSimilarities : null);
    };

    fetchAllSimilarities();
  }, [selectedCollectionsIndex, customCollections]);

  const handleSortTable = (column) => {
    sortByColumn(column);
  };

  if (!collections) {
    return <div className="alert alert-warning">Failed to load collection data.</div>;
  }

  return (
    <div className='mb-5'>
      <div className='row'>
        <div className='col-12'>
          <div className='d-flex align-items-end justify-content-between'>
            <h4 className='fw-light'>Seqcol Comparison Overview Module (SCOM)</h4>
          </div>

          <div className='mt-2 mb-0 text-muted'>
            <p className='mb-2'>
              This tool provides summary similarity metrics for comparisons between
              all sequence collections on the server and one of your choice.
            </p>

            <p className='mb-2'>Two easy ways to use this tool:</p>

            <ol className='mb-0'>
              <li>
                If you have a FASTA file, compare it against assemblies on the
                server using the in-browser <a href='/fasta'>FASTADigest</a> tool.
              </li>
              <li>
                If you already have the refget sequence collection JSON output
                (e.g. from <code>refget fasta seqcol yourfasta.fa</code>), paste it
                in the text box below.
              </li>
            </ol>
          </div>
          <div className='row mt-4'>
            <div
              className={`${relationship === 'manyToMany' ? 'col-6' : 'col-12'}`}
            >
              <div className='card'>
                <div className='card-header tiny d-flex justify-content-between'>
                  <span className='fw-bold'>Custom Collection Output</span>
                  <button
                    className='btn btn-success btn-xs shadow-sm ms-auto'
                    disabled={isLoading}
                    onClick={async () =>
                      handleAddCustomCollection(
                        customCollectionJSON,
                        customCollectionName,
                      )
                    }
                  >
                    {isLoading ? 'Loading...' : (relationship === 'oneToMany' ? 'Submit' : 'Add')}
                  </button>
                  <button
                    className='btn btn-secondary btn-xs shadow-sm ms-1'
                    disabled={isLoading}
                    onClick={async () => {
                      setCustomCollectionJSON(JSON.stringify(sampleJSON, null, 4));
                      handleAddCustomCollection(
                        JSON.stringify(sampleJSON),
                        customCollectionName,
                      )
                    }}
                  >
                    Example
                  </button>
                </div>
                <input
                  id='custom-collection-name'
                  type='text'
                  onChange={(e) => setCustomCollectionName(e.target.value)}
                  placeholder='Name or digest of custom collection (optional)'
                  className='form-control tiny border-0 rounded-0 border-bottom z-active'
                />
                <div className='d-flex align-items-center border-bottom px-2 py-1 tiny'>
                  <span className='text-muted me-2'>Compare with:</span>
                  <div className='btn-group btn-group-sm'>
                    <button
                      type='button'
                      className={`btn ${species === 'human' ? 'btn-primary' : 'btn-outline-secondary'}`}
                      onClick={() => setSpecies('human')}
                    >
                      Human
                    </button>
                    <button
                      type='button'
                      className={`btn ${species === 'mouse' ? 'btn-primary' : 'btn-outline-secondary'}`}
                      onClick={() => setSpecies('mouse')}
                    >
                      Mouse
                    </button>
                  </div>
                </div>
                <textarea
                  id='custom-collection-json'
                  onChange={(e) => setCustomCollectionJSON(e.target.value)}
                  value={customCollectionJSON}
                  placeholder='Paste output from `refget fasta seqcol yourfasta.fa` here.'
                  className='form-control tiny border-0 rounded-0 rounded-bottom z-active'
                  rows='12'
                />
              </div>
            </div>

          </div>
        </div>
      </div>

      {storeError && (
        <div className='alert alert-danger mt-3 d-flex justify-content-between align-items-center' role='alert'>
          <div>
            <i className='bi bi-exclamation-triangle me-2'></i>
            <strong>Error:</strong> {storeError}
          </div>
          <button
            className='btn btn-sm btn-outline-danger'
            onClick={() => setStoreError(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {(similarities && !isLoading) ? (
        <div className='row'>
          <div className='col-12'>
            <div className='d-flex align-items-start justify-content-between mt-4 mb-2'>
              <h5 className='fw-light'>Strip Plot</h5>
              <select
                className='form-select form-select-sm ms-auto tiny'
                style={{width: '12%'}}
                aria-label='strip-orientation'
                value={stripOrientation}
                onChange={(e) => setStripOrientation(e.target.value)}
              >
                <option value='horizontal'>Horizontal Plot</option>
                <option value='vertical'>Vertical Plot</option>
              </select>
              <select
                className='form-select form-select-sm ms-1 tiny'
                style={{width: '12%'}}
                aria-label='strip-jitter'
                value={stripJitter}
                onChange={(e) => setStripJitter(e.target.value)}
              >
                <option value='none'>Stacked Points</option>
                {relationship === 'manyToMany' && (
                  <option value='uniform'>Uniformly Distributed Points</option>
                )}
                {relationship === 'oneToMany' && (
                  <option value='bars'>Bars</option>
                )}
              </select>
            </div>
            <StripPlot
              similarities={similarities.map(({ raw, ...rest }) => rest)}
              jitter={stripJitter}
              pointSize={
                relationship === 'oneToMany' || selectedCollections.length <= 1
                  ? 'big'
                  : 'normal'
              }
              orientation={stripOrientation}
            />

            <div className='d-flex align-items-end justify-content-between mt-5 mb-2'>
              <h5 className='fw-light'>Heatmap</h5>
            </div>
            <MultiMetricHeatmapPlot similarities={similarities.map(({ raw, ...rest }) => rest)} />

            <div className='d-flex align-items-end justify-content-between'>
              <h5 className='fw-light mt-5'>Seqcol Comparison Summary Table</h5>
              <p className='mb-2 text-muted'>
                Click on a row to view a detailed 1-1 comparison in SCIM.
              </p>
            </div>
            <div className='rounded shadow-sm border tiny overflow-x-auto'>
              <table className='table table-striped table-hover table-rounded'>
                <thead>
                  <tr>
                    <th className='cursor-pointer text-nowrap' onClick={() => handleSortTable('comparedAlias')}>Compared Seqcol <i className={sortBy === 'comparedAlias' ? (sortAscending ? 'bi bi-sort-up' : 'bi bi-sort-down') : 'bi bi-filter'} /></th>
                    <th className='cursor-pointer text-nowrap' onClick={() => handleSortTable('comparedDigest')}>Compared Seqcol Digest <i className={sortBy === 'comparedDigest' ? (sortAscending ? 'bi bi-sort-up' : 'bi bi-sort-down') : 'bi bi-filter'} /></th>
                    <th className='cursor-pointer text-nowrap' onClick={() => handleSortTable('lengths')}>Lengths <i className={sortBy === 'lengths' ? (sortAscending ? 'bi bi-sort-up' : 'bi bi-sort-down') : 'bi bi-filter'} /></th>
                    <th className='cursor-pointer text-nowrap' onClick={() => handleSortTable('name_length_pairs')}>Name Length Pairs <i className={sortBy === 'name_length_pairs' ? (sortAscending ? 'bi bi-sort-up' : 'bi bi-sort-down') : 'bi bi-filter'} /></th>
                    <th className='cursor-pointer text-nowrap' onClick={() => handleSortTable('names')}>Names <i className={sortBy === 'names' ? (sortAscending ? 'bi bi-sort-up' : 'bi bi-sort-down') : 'bi bi-filter'} /></th>
                    <th className='cursor-pointer text-nowrap' onClick={() => handleSortTable('sequences')}>Sequences <i className={sortBy === 'sequences' ? (sortAscending ? 'bi bi-sort-up' : 'bi bi-sort-down') : 'bi bi-filter'} /></th>
                    <th className='cursor-pointer text-nowrap' onClick={() => handleSortTable('sorted_sequences')}>Sorted Sequences <i className={sortBy === 'sorted_sequences' ? (sortAscending ? 'bi bi-sort-up' : 'bi bi-sort-down') : 'bi bi-filter'} /></th>
                  </tr>
                </thead>
                <tbody>
                  {similarities?.map((row, index) => (
                    <tr
                      key={index}
                      className='cursor-pointer'
                      onClick={() => handleNavigateSCIM(row)}
                    >
                      <td>{row.comparedAlias ? row.comparedAlias : row.comparedDigest}</td>
                      <td>{row.comparedDigest}</td>
                      <td>{row.lengths != null ? (Number.isInteger(row.lengths) ? row.lengths : row.lengths.toFixed(3)) : '-'}</td>
                      <td>{row.name_length_pairs != null ? (Number.isInteger(row.name_length_pairs) ? row.name_length_pairs : row.name_length_pairs.toFixed(3)) : '-'}</td>
                      <td>{row.names != null ? (Number.isInteger(row.names) ? row.names : row.names.toFixed(3)) : '-'}</td>
                      <td>{row.sequences != null ? (Number.isInteger(row.sequences) ? row.sequences : row.sequences.toFixed(3)) : '-'}</td>
                      <td>{row.sorted_sequences != null ? (Number.isInteger(row.sorted_sequences) ? row.sorted_sequences : row.sorted_sequences.toFixed(3)) : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        (selectedCollections.length > 0 || isLoading)  && <p className='mt-4'>Loading...</p>
      )}
    </div>
  );
};

export { SCOM };
