import { useEffect, useRef } from 'react';
import embed from 'vega-embed';

import { snakeToTitle } from '../utilities';

const HeatmapPlot = ({ similarities, metric }) => {
  const plotRef = useRef(null);

  const selectedCount = [...new Set(similarities.map((e) => e.selectedDigest))]
    .length;

  const heatmapSpec = (similarities, metric) => {
    return {
      $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
      data: {
        values: similarities,
      },
      mark: {
        type: 'rect',
        stroke: '#333',
        strokeWidth: 1,
      },
      encoding: {
        x: {
          field: 'comparedDigest',
          type: 'nominal',
          title: 'Compared Digest',
          sort: null,
          axis: {
            labelAngle: -33,
            labelLimit: 111,
            domain: false,
          },
        },
        y: {
          field: 'selectedDigest',
          type: 'nominal',
          title: 'Selected Digest',
          sort: null,
          axis: {
            labelAngle: -33,
            labelLimit: 111,
            domain: false,
          },
        },
        color: {
          field: metric,
          type: 'quantitative',
          title: 'Jaccard Similarity',
          scale: {
            scheme: 'bluepurple',
            reverse: false,
            domain: [0, 1],
          },
          legend: {
            format: '.2f',
          },
        },
        tooltip: [
          { field: 'selectedDigest', title: 'Selected' },
          { field: 'comparedDigest', title: 'Compared' },
          { field: metric, title: snakeToTitle(metric), format: '.3f' },
        ],
      },
      width: 'container',
      height:
        selectedCount < 10
          ? 50 * selectedCount
          : selectedCount < 20
            ? 22 * selectedCount
            : 13 * selectedCount,
    };
  };

  useEffect(() => {
    if (plotRef.current && similarities && metric) {
      const spec = heatmapSpec(similarities, metric);
      try {
        embed(plotRef.current, spec, {
          actions: true,
          config: {
            // Force Vega to use relative URLs for gradients
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
  }, [similarities, metric]);

  return <div className='w-100' ref={plotRef} />;
};

export { HeatmapPlot };
