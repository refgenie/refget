import { useEffect, useRef } from 'react';
import embed from 'vega-embed';

const ScatterPlot = ({ similarities }) => {
  const plotRef = useRef(null);

  const scatterSpec = (similarities) => {
 // Create all pairwise combinations of metrics
 const metrics = ['lengths', 'name_length_pairs', 'names', 'sequences', 'sorted_sequences'];
 const scatterData = [];
 
 similarities.forEach(row => {
   metrics.forEach(xMetric => {
     metrics.forEach(yMetric => {
       if (row[xMetric] !== null && row[xMetric] !== undefined && 
           row[yMetric] !== null && row[yMetric] !== undefined) {
         scatterData.push({
           pairId: `${row.selectedDigest}_${row.comparedDigest}`,
           selectedDigest: row.selectedDigest,
           comparedDigest: row.comparedDigest,
           xMetric: xMetric,
           yMetric: yMetric,
           xValue: row[xMetric],
           yValue: row[yMetric],
           isDiagonal: xMetric === yMetric
         });
       }
     });
   });
 });

 return {
   $schema: "https://vega.github.io/schema/vega-lite/v5.json",
   data: {
     values: scatterData
   },
   mark: {
     type: "circle",
     size: 40,
     opacity: 0.6
   },
   encoding: {
     x: {
       field: "xValue",
       type: "quantitative",
       title: null,
       scale: {
         domain: [0, 1]
       },
       axis: {
         grid: true,
         tickCount: 3
       }
     },
     y: {
       field: "yValue",
       type: "quantitative",
       title: null,
       scale: {
         domain: [0, 1]
       },
       axis: {
         grid: true,
         tickCount: 3
       }
     },
     color: {
       condition: {
         test: "datum.isDiagonal",
         value: "#999999"
       },
       field: "xValue",
       type: "quantitative",
       scale: {
         scheme: "viridis",
         domain: [0, 1]
       },
       legend: {
         title: "Similarity Score"
       }
     },
     opacity: {
       condition: {
         test: "datum.isDiagonal",
         value: 0.3
       },
       value: 0.7
     },
     column: {
       field: "xMetric",
       type: "nominal",
       title: null,
       header: {
         labelAngle: -45,
         labelAlign: "right",
         labelFontSize: 10
       }
     },
     row: {
       field: "yMetric",
       type: "nominal",
       title: null,
       header: {
         labelAngle: 0,
         labelAlign: "right",
         labelFontSize: 10
       }
     },
     tooltip: [
       {field: "selectedDigest", title: "Selected"},
       {field: "comparedDigest", title: "Compared"},
       {field: "xMetric", title: "X Metric"},
       {field: "yMetric", title: "Y Metric"},
       {field: "xValue", title: "X Value", format: ".3f"},
       {field: "yValue", title: "Y Value", format: ".3f"}
     ]
   },
   resolve: {
     scale: {
       color: "shared"
     }
   },
   width: 80,
   height: 80
 };
}

  useEffect(() => {
    if (plotRef.current && similarities) {
      const spec = scatterSpec(similarities);
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
  }, [similarities]);

  return (
    <div className='w-100' ref={plotRef} />
  );
  
}

export { ScatterPlot };
