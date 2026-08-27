import { useCallback, useEffect, useRef } from 'react';
import embed from 'vega-embed';
import type { VisualizationSpec } from 'vega-embed';
import type { SimilarityRow } from '../types';
import { asSpec, asEmbedOptions } from '../utils/vega';

import { snakeToTitle } from '../utilities';

interface MultiMetricHeatmapPlotProps {
  similarities: SimilarityRow[];
  metrics?: string[];
}

/** One cell of the long-form matrix the heatmap is drawn from. */
interface MetricCell {
  comparedSeqcol: string;
  comparedDigest: string;
  inputSeqcol: string | undefined;
  metric: string;
  metricTitle: string;
  value: unknown;
}

const MultiMetricHeatmapPlot = ({
  similarities,
  metrics = ['lengths', 'name_length_pairs', 'names', 'sequences', 'sorted_sequences'],
}: MultiMetricHeatmapPlotProps) => {
  const plotRef = useRef<HTMLDivElement>(null);

  const transformData = useCallback((rows: SimilarityRow[], metricKeys: string[]) => {
    const transformedData: MetricCell[] = [];

    rows.forEach((row) => {
      metricKeys.forEach((metric) => {
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
  }, []);

  const metricCount = metrics.length;

  const heatmapSpec = useCallback((rows: SimilarityRow[], metricKeys: string[]): VisualizationSpec => {
    const transformedData = transformData(rows, metricKeys);

    return asSpec({
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
          sort: metricKeys.map((m) => snakeToTitle(m)),
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
    });
  }, [transformData, metricCount]);

  useEffect(() => {
    const node = plotRef.current;
    if (node && similarities && metrics.length > 0) {
      const spec = heatmapSpec(similarities, metrics);
      try {
        embed(node, spec, asEmbedOptions({
          actions: true,
          config: {
            baseURL: '',
          },
        })).catch((error: unknown) => {
          console.error('Embed error after parsing:', error);
        });
      } catch (error) {
        console.error(error);
      }
    }

    return () => {
      if (node) {
        node.innerHTML = '';
      }
    };
  }, [similarities, metrics, heatmapSpec]);

  return <div className='w-full' ref={plotRef} />;
};

export { MultiMetricHeatmapPlot };

