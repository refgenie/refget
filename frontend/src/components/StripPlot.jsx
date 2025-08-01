import { useEffect, useRef } from 'react';
import embed from 'vega-embed';

import { snakeToTitle } from '../utilities';

const StripPlot = ({ similarities, jitter = 'none', pointSize = 'normal' }) => {
  const plotRef = useRef(null);

  // const comparedCount = [...new Set(similarities.map((e) => e.comparedDigest))].length;
  const metrics = [
    'lengths',
    'sequences',
    'sorted_sequences',
    'name_length_pairs',
    'names',
  ];

  const getPlottedRowCount = (similarities, metrics) => {
    const rowsWithData = new Set();
    
    similarities.forEach((item) => {
      const hasAnyMetric = metrics.some(metric => item[metric] !== undefined && item[metric] !== null);
      if (hasAnyMetric) {
        rowsWithData.add(item.comparedDigest);
      }
    });
    
    return rowsWithData.size;
  };
  const plottedRowCount = getPlottedRowCount(similarities, metrics);

  const stripSpec = (similarities, jitter, pointSize) => {
    const transformedData = similarities.flatMap((item) => {
      return metrics
        .filter((metric) => item[metric] !== undefined)
        .map((metric) => ({
          selectedDigest: item.selectedDigest,
          comparedDigest: item.comparedDigest,
          metric: snakeToTitle(metric),
          value: item[metric],
          custom: item.custom,
          jitter:
            jitter === 'uniform'
              ? Math.random()
              : jitter === 'normal'
                ? Math.sqrt(-2 * Math.log(Math.random())) *
                  Math.cos(2 * Math.PI * Math.random())
                : 0,
        }));
    });

    if (jitter === 'bars') {
      return {
        $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
        data: {
          values: transformedData,
        },
        params: [
          {
            name: 'metric_selection',
            select: {
              type: 'point',
              fields: ['metric'],
            },
            bind: 'legend',
          },
        ],
        mark: {
          type: 'bar',
          tooltip: true,
        },
        encoding: {
          x: {
            field: 'value',
            type: 'quantitative',
            title: 'Similarity Score',
            scale: { domain: [0, 1] },
          },
          y: {
            field: 'comparedDigest',
            type: 'nominal',
            title: 'Compared Digest',
            axis: {
              labelAngle: -33,
              labelLimit: 111,
              grid: false,
            },
          },
          yOffset: {
            field: 'metric',
            type: 'nominal',
          },
          color: {
            field: 'metric',
            type: 'nominal',
            title: 'Metric',
            legend: {
              orient: 'right',
            },
          },
          opacity: {
            condition: [
              {
                test: "!length(data('metric_selection_store'))",
                value: 0.8,
              },
              {
                param: 'metric_selection',
                value: 1,
              },
            ],
            value: 0.1,
          },
          tooltip: [
            { field: 'selectedDigest', title: 'Selected' },
            { field: 'comparedDigest', title: 'Compared' },
            { field: 'metric', title: 'Metric' },
            { field: 'value', title: 'Value', format: '.3f' },
          ],
        },
        width: 'container',
        height: 50 * plottedRowCount,
      };
    }

    return {
      $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
      data: {
        values: transformedData,
      },
      layer: [
        {
          mark: {
            type: 'rule',
            strokeWidth: 1.3,
            color: '#888',
          },
          encoding: {
            x: {
              field: 'value',
              type: 'quantitative',
            },
            x2: {
              value: 0,
            },
            y: {
              field: 'comparedDigest',
              type: 'nominal',
            },
            opacity:
              jitter === 'none'
                ? {
                    condition: [
                      {
                        test: "!length(data('metric_selection_store'))",
                        value: 1,
                      },
                      {
                        param: 'metric_selection',
                        value: 1,
                      },
                    ],
                    value: 0,
                  }
                : { value: 0 },
            yOffset:
              jitter === 'none'
                ? null
                : { field: 'jitter', type: 'quantitative' },
          },
        },
        {
          params: [
            {
              name: 'metric_selection',
              select: {
                type: 'point',
                fields: ['metric'],
              },
              bind: 'legend',
            },
          ],
          mark: {
            type: 'point',
            filled: true,
          },
          encoding: {
            x: {
              field: 'value',
              type: 'quantitative',
              title: 'Similarity Score',
              scale: { domain: [0, 1] },
            },
            y: {
              field: 'comparedDigest',
              type: 'nominal',
              title: 'Compared Digest',
              axis: {
                labelAngle: -33,
                labelLimit: 111,
                grid: true,
              },
            },
            color: {
              field: 'metric',
              type: 'nominal',
              title: 'Metric',
              legend: {
                orient: 'right',
              },
            },
            shape: {
              field: 'metric',
              type: 'nominal',
              title: 'Metric',
              domain: metrics.map((m) => snakeToTitle(m)),
              range: ['circle', 'square', 'triangle-up', 'diamond', 'cross'],
              legend: {
                orient: 'right',
              },
            },
            opacity: {
              condition: [
                {
                  test: "!length(data('metric_selection_store'))",
                  value: 0.8,
                },
                {
                  param: 'metric_selection',
                  value: 1,
                },
              ],
              value: 0.05,
            },
            size: {
              condition: [
                {
                  test: "!length(data('metric_selection_store'))",
                  value: pointSize === 'big' ? 88 : 44,
                },
                {
                  param: 'metric_selection',
                  value: pointSize === 'big' ? 132 : 66,
                },
              ],
              value: 44,
            },
            yOffset:
              jitter === 'none'
                ? null
                : { field: 'jitter', type: 'quantitative' },
          },
        },
        {
          mark: {
            type: 'point',
            filled: true,
          },
          encoding: {
            x: {
              field: 'value',
              type: 'quantitative',
              title: 'Similarity Score',
              scale: { domain: [0, 1] },
            },
            y: {
              field: 'comparedDigest',
              type: 'nominal',
              title: 'Compared Digest',
              axis: {
                labelAngle: -33,
                labelLimit: 111,
                grid: true,
              },
            },
            color: {
              field: 'metric',
              type: 'nominal',
              title: 'Metric',
              legend: {
                orient: 'right',
              },
            },
            shape: {
              field: 'metric',
              type: 'nominal',
              title: 'Metric',
              domain: metrics.map((m) => snakeToTitle(m)),
              range: ['circle', 'square', 'triangle-up', 'diamond', 'cross'],
              legend: {
                orient: 'right',
              },
            },
            opacity: {
              value: 0,
            },
            size: {
              condition: [
                {
                  test: "!length(data('metric_selection_store'))",
                  value: pointSize === 'big' ? 88 : 44,
                },
                {
                  param: 'metric_selection',
                  value: pointSize === 'big' ? 132 : 66,
                },
              ],
              value: 0,
            },
            yOffset:
              jitter === 'none'
                ? null
                : { field: 'jitter', type: 'quantitative' },
            tooltip: [
              { field: 'selectedDigest', title: 'Selected' },
              { field: 'comparedDigest', title: 'Compared' },
              { field: 'metric', title: 'Metric' },
              { field: 'value', title: 'Value' },
            ],
          },
        },
      ],
      width: 'container',
      height: 50 * plottedRowCount,
    };
  };

  useEffect(() => {
    if (plotRef.current && similarities) {
      const spec = stripSpec(similarities, jitter, pointSize);
      try {
        embed(plotRef.current, spec, { actions: true }).catch((error) => {
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

  return <div className='w-100' ref={plotRef} />;
};

export { StripPlot };
