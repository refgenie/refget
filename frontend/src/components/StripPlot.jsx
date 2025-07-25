import { useEffect, useRef } from 'react';
import embed from 'vega-embed';

import { snakeToTitle } from '../utilities';


const StripPlot = ({ similarities, jitter = 'none' }) => {
  const plotRef = useRef(null);
  
  const comparedCount = [...new Set(similarities.map(e => e.comparedDigest))].length;
  const metrics = ['lengths', 'sequences', 'sorted_sequences', 'name_length_pairs', 'names'];

  const stripSpec = (similarities, jitter) => {

    const transformedData = similarities.flatMap(item => {
      return metrics
        .filter(metric => item[metric] !== undefined)
        .map(metric => ({
          selectedDigest: item.selectedDigest,
          comparedDigest: item.comparedDigest,
          metric: snakeToTitle(metric),
          value: item[metric],
          custom: item.custom,
          jitter: jitter === 'uniform' 
            ? Math.random() 
            : jitter === 'normal' 
              ? Math.sqrt(-2 * Math.log(Math.random())) * Math.cos(2 * Math.PI * Math.random())
              : 0
        }));
    });

    return {
      $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
      data: {
        values: transformedData
      },
      layer: [
        {
          mark: {
            type: 'rule',
            strokeWidth: 1.3,
            color: '#888'
          },
          encoding: {
            x: {
              field: 'value',
              type: 'quantitative'
            },
            x2: {
              value: 0
            },
            y: {
              field: 'comparedDigest',
              type: 'nominal'
            },
            opacity: jitter === 'none' ? {
              condition: [
                {
                  test: "!length(data('metric_selection_store'))",
                  value: 1
                },
                {
                  param: 'metric_selection',
                  value: 1
                }
              ],
              value: 0
            } : {value: 0},
            yOffset: jitter === 'none' ? null : { field: 'jitter', type: 'quantitative' },
          }
        },
        {
          params: [
            {
              name: 'metric_selection',
              select: {
                type: 'point',
                fields: ['metric'],
              },
              bind: 'legend'
            }
          ],
          mark: {
            type: 'point',
            filled: true
          },
          encoding: {
            x: {
              field: 'value',
              type: 'quantitative',
              title: 'Similarity Score',
              scale: {domain: [0, 1]}
            },
            y: {
              field: 'comparedDigest',
              type: 'nominal',
              title: 'Compared Digest',
              axis: {
                labelAngle: -33,
                labelLimit: 111,
                grid: true
              }
            },
            color: {
              field: 'metric',
              type: 'nominal',
              title: 'Metric',
              legend: {
                orient: 'right'
              }
            },
            shape: {
              field: 'metric',
              type: 'nominal',
              title: 'Metric',
              domain: metrics.map(m => snakeToTitle(m)),
              range: ['circle', 'square', 'triangle-up', 'diamond', 'cross'],
              legend: {
                orient: 'right'
              }
            },
            opacity: {
              condition: [
                {
                  test: "!length(data('metric_selection_store'))",
                  value: 0.8
                },
                {
                  param: 'metric_selection',
                  value: 1
                }
              ],
              value: 0.05
            },
            size: {
              condition: [
                {
                  test: "!length(data('metric_selection_store'))",
                  value: 44
                },
                {
                  param: 'metric_selection',
                  value: 66
                }
              ],
              value: 44
            },
            yOffset: jitter === 'none' ? null : { field: 'jitter', type: 'quantitative' },
          }
        },
        {
          mark: {
            type: 'point',
            filled: true
          },
          encoding: {
            x: {
              field: 'value',
              type: 'quantitative',
              title: 'Similarity Score',
              scale: {domain: [0, 1]}
            },
            y: {
              field: 'comparedDigest',
              type: 'nominal',
              title: 'Compared Digest',
              axis: {
                labelAngle: -33,
                labelLimit: 111,
                grid: true
              }
            },
            color: {
              field: 'metric',
              type: 'nominal',
              title: 'Metric',
              legend: {
                orient: 'right'
              }
            },
            shape: {
              field: 'metric',
              type: 'nominal',
              title: 'Metric',
              domain: metrics.map(m => snakeToTitle(m)),
              range: ['circle', 'square', 'triangle-up', 'diamond', 'cross'],
              legend: {
                orient: 'right'
              }
            },
            opacity: {
              value: 0
            },
            size: {
              condition: [
                {
                  test: "!length(data('metric_selection_store'))",
                  value: 44
                },
                {
                  param: 'metric_selection',
                  value: 66
                }
              ],
              value: 0
            },
            yOffset: jitter === 'none' ? null : { field: 'jitter', type: 'quantitative' },
            tooltip: [
              {field: 'selectedDigest', title: 'Selected'},
              {field: 'comparedDigest', title: 'Compared'},
              {field: 'metric', title: 'Metric'},
              {field: 'value', title: 'Value'},
            ]
          }
        },
      ],
      width: 'container',
      height: 60 * comparedCount
    };
  }

  useEffect(() => {
    if (plotRef.current && similarities) {
      const spec = stripSpec(similarities, jitter);
      try {
        embed(plotRef.current, spec, { actions: true })
          .catch(error => {
            console.error('Embed error after parsing:', error);
          });
      } catch (error) {
        console.error(error);
      }
    }

    return () => {
      if (plotRef.current) {
        plotRef.current.innerHTML = '';
      }
    };
  }, [similarities, jitter]);

  return (
    <div className='w-100' ref={plotRef} />
  );
  
}

export { StripPlot };
