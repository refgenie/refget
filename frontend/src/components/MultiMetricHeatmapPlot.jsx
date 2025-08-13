import { useEffect, useRef } from 'react';
import embed from 'vega-embed';

import { snakeToTitle } from '../utilities';

const MultiMetricHeatmapPlot = ({ similarities, metrics = ['lengths', 'name_length_pairs', 'names', 'sequences', 'sorted_sequences'] }) => {
  const plotRef = useRef(null);

  const transformData = (similarities, metrics) => {
    const transformedData = [];
    
    similarities.forEach(row => {
      metrics.forEach(metric => {
        transformedData.push({
          comparedSeqcol: row.comparedAlias ? row.comparedAlias : row.comparedDigest,
          comparedDigest: row.comparedDigest,
          inputSeqcol: row.selectedDigest,
          metric: metric,
          metricTitle: snakeToTitle(metric),
          value: row[metric]
        });
      });
    });
    
    return transformedData;
  };

  const metricCount = metrics.length;

  const heatmapSpec = (similarities, metrics) => {
    const transformedData = transformData(similarities, metrics);
    
    return {
      $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
      data: {
        values: transformedData,
      },
      mark: {
        type: 'rect',
        stroke: '#333',
        strokeWidth: 1,
      },
      encoding: {
        x: {
          field: 'comparedSeqcol',
          type: 'nominal',
          title: 'Compared Sequence Collection',
          sort: false,
          axis: {
            domain: false,
            labels: false,
            ticks: false
          },
        },
        y: {
          field: 'metricTitle',
          type: 'nominal',
          title: 'Metrics',
          sort: metrics.map(m => snakeToTitle(m)),
          axis: {
            domain: false,
            labelLimit: 150,
          },
        },
        color: {
          field: 'value',
          type: 'quantitative',
          title: 'Jaccard Similarity',
          scale: {
            scheme: 'bluepurple',
            reverse: false,
            domain: [0, 1],
          },
          legend: {
            format: '.2f'
          },
        },
        tooltip: [
          // { field: 'inputSeqcol', title: 'Selected' },
          { field: 'comparedSeqcol', title: 'Compared Seqcol' },
          { field: 'comparedDigest', title: 'Compared Seqcol Digest' },
          { field: 'metricTitle', title: 'Metric' },
          { field: 'value', title: 'Similarity', format: '.3f' },
        ],
      },
      config: {
        legend: {
          orient: 'bottom',
          layout: {
            bottom: {
              anchor: 'end'
            }
          },
          titleAlign: 'right',
          titleAnchor: 'end',
          titlePadding: 2.5,
          offset: -5,
        },
      },
      width: 'container',
      height: metricCount * 15,
    };
  };

  useEffect(() => {
    if (plotRef.current && similarities && metrics.length > 0) {
      const spec = heatmapSpec(similarities, metrics);
      try {
        embed(plotRef.current, spec, {
          actions: true,
          config: {
            baseURL: '',
          },
        }).catch((error) => {
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
  }, [similarities, metrics]);

  return <div className='w-100' ref={plotRef} />;
};

export { MultiMetricHeatmapPlot };

