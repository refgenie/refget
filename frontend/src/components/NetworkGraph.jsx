import { useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';

import { snakeToTitle } from '../utilities';


const NetworkGraph = ({ similarities, metric = 'sequences', tension = 0.1, threshold = 0.0 }) => {
  const svgRef = useRef(null);

  const selectedCount = [...new Set(similarities.map(e => e.selectedDigest))].length;

  const drawNetwork = useCallback(() => {
    if (!svgRef.current || !similarities || similarities.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Get container dimensions
    const containerRect = svgRef.current.getBoundingClientRect();
    const width = containerRect.width || 800;
    const height = containerRect.height || 600;
    const radius = Math.min(width, height) * 0.35;

    // Set SVG dimensions
    svg.attr('width', width).attr('height', height);

    const container = svg.append('g');

    // Create radial gradient for background circle
    const defs = svg.append('defs');
    const gradient = defs.append('radialGradient')
      .attr('id', 'background-gradient')
      .attr('cx', '50%')
      .attr('cy', '50%')
      .attr('r', '50%');

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#ffeaa7')
      .attr('stop-opacity', 0.33);

    gradient.append('stop')
      .attr('offset', '67%')
      .attr('stop-color', '#ffeaa7')
      .attr('stop-opacity', 0.11);

    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#ffeaa7')
      .attr('stop-opacity', 0);

    // Add background circle
    container.append('circle')
      .attr('cx', width / 2)
      .attr('cy', height / 2)
      .attr('r', radius + 100)
      .style('fill', 'url(#background-gradient)')
      .style('pointer-events', 'none');

    // Filter similarities by threshold and exclude self-connections
    const filteredSimilarities = similarities.filter(d => 
      d[metric] !== null && d[metric] !== undefined && d[metric] >= threshold &&
      d.selectedDigest !== d.comparedDigest // Exclude self-connections
    );
    if (filteredSimilarities.length === 0) {
      // Draw empty state
      container.append('text')
        .attr('x', width/2)
        .attr('y', height/2)
        .attr('text-anchor', 'middle')
        .style('font-size', '16px')
        .style('fill', '#666')
        .text('No connections meet the threshold');
      return;
    }

    // Get unique nodes from filtered data
    const nodeSet = new Set();
    filteredSimilarities.forEach(d => {
      nodeSet.add(d.selectedDigest);
      nodeSet.add(d.comparedDigest);
    });
    const nodes = Array.from(nodeSet);

    // Position nodes in circle
    const nodePositions = {};
    nodes.forEach((node, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI;
      nodePositions[node] = {
        x: width/2 + Math.cos(angle) * radius,
        y: height/2 + Math.sin(angle) * radius,
        angle: angle,
        id: node,
        shortId: node.substring(0, 10) + "..."
      };
    });

    // Count connections from filtered data
    const connectionCount = {};
    nodes.forEach(node => connectionCount[node] = 0);
    filteredSimilarities.forEach(d => {
      connectionCount[d.selectedDigest]++;
      connectionCount[d.comparedDigest]++;
    });

    // Create tooltip
    const tooltip = d3.select('body').selectAll('.network-tooltip')
      .data([0])
      .join('div')
      .attr('class', 'network-tooltip')
      .style('position', 'absolute')
      .style('padding', '8px 12px')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000')
      .style('opacity', 0);

    // Draw connections
    container.selectAll('.connection-line')
      .data(filteredSimilarities)
      .enter().append('path')
      .attr('class', 'connection-line')
      .attr('d', d => {
        const source = nodePositions[d.selectedDigest];
        const target = nodePositions[d.comparedDigest];
        
        if (tension === 0) {
          return `M${source.x},${source.y} L${target.x},${target.y}`;
        } else {
          const centerX = width / 2;
          const centerY = height / 2;
          const midX = (source.x + target.x) / 2;
          const midY = (source.y + target.y) / 2;
          
          const controlX = midX + (centerX - midX) * tension;
          const controlY = midY + (centerY - midY) * tension;
          
          return `M${source.x},${source.y} Q${controlX},${controlY} ${target.x},${target.y}`;
        }
      })
      .style('stroke', d => d3.interpolateBuPu(d[metric] || 0))
      .style('stroke-width', selectedCount > 6 ? 1.5 : 2.25)
      .style('fill', 'none')
      .style('opacity', 0.7)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        d3.select(this).style('opacity', 1.0).style('stroke-width', 3);
        
        tooltip.transition().duration(200).style('opacity', 0.9);
        tooltip.html(`
          <strong>Digest 1:</strong> ${nodePositions[d.selectedDigest].id}<br/>
          <strong>Digest 2:</strong> ${nodePositions[d.comparedDigest].id}<br/>
          <strong>${snakeToTitle(metric)}:</strong> ${(d[metric] || 0).toFixed(3)}
        `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this).style('opacity', 0.7).style('stroke-width', 2);
        tooltip.transition().duration(500).style('opacity', 0);
      });

    // Draw nodes
    container.selectAll('.digest-point')
      .data(Object.values(nodePositions))
      .enter().append('circle')
      .attr('class', 'digest-point')
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .attr('r', d => 6)
      .style('fill', 'black')
      .style('stroke', 'white')
      .style('stroke-width', 3)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        // d3.select(this).style('stroke-width', 3);
        
        tooltip.transition().duration(200).style('opacity', 0.9);
        tooltip.html(`
          <strong>Digest:</strong><br/>
          ${d.id}<br/>
        `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', function() {
      //   d3.select(this).style('stroke-width', 2);
        tooltip.transition().duration(500).style('opacity', 0);
      });

    // Add labels
    container.selectAll('.digest-label')
      .data(Object.values(nodePositions))
      .enter().append('text')
      .attr('class', 'digest-label')
      .attr('x', d => {
        const labelRadius = radius + 20;
        return width/2 + Math.cos(d.angle) * labelRadius;
      })
      .attr('y', d => {
        const labelRadius = radius + 20;
        return height/2 + Math.sin(d.angle) * labelRadius;
      })
      .attr('dy', '0.35em')
      .style('text-anchor', d => {
        if (d.angle > Math.PI/2 && d.angle < 3*Math.PI/2) return 'end';
        return 'start';
      })
      .attr('transform', d => {
        const labelRadius = radius + 20;
        const x = width/2 + Math.cos(d.angle) * labelRadius;
        const y = height/2 + Math.sin(d.angle) * labelRadius;
        const rotation = d.angle > Math.PI/2 && d.angle < 3*Math.PI/2 ? 
          (d.angle * 180/Math.PI + 180) : (d.angle * 180/Math.PI);
        return `rotate(${rotation}, ${x}, ${y})`;
      })
      .style('font-size', '10px')
      .style('font-weight', 'bold')
      .style('fill', '#333')
      .style('pointer-events', 'none')
      .text(d => d.shortId);

  }, [similarities, metric, tension, threshold]);
  
  useEffect(() => {
    // Initial draw
    drawNetwork();

    // Add resize event listener
    const handleResize = () => {
      // Debounce the resize event to avoid excessive re-renders
      clearTimeout(window.resizeTimeout);
      window.resizeTimeout = setTimeout(drawNetwork, 150);
    };

    window.addEventListener('resize', handleResize);
    
    // Optional: Listen for orientation changes on mobile devices
    window.addEventListener('orientationchange', () => {
      setTimeout(drawNetwork, 100); // Small delay for orientation change
    });

    // Cleanup event listeners on unmount
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', drawNetwork);
      if (window.resizeTimeout) {
        clearTimeout(window.resizeTimeout);
      }
      // Clean up tooltip
      d3.select('body').selectAll('.network-tooltip').remove();
    };
  }, [drawNetwork]);

  // Clean up tooltip on unmount
  useEffect(() => {
    return () => {
      d3.select('body').selectAll('.network-tooltip').remove();
    };
  }, []);

  return (
    <div className="w-100">
      <svg 
        ref={svgRef} 
        className="w-100"
        style={{ minHeight: '600px' }}
      />
    </div>
  );
};

export { NetworkGraph };