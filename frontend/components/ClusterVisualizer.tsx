'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

interface Community {
  id: number;
  title: string;
  summary: string;
  nodes: string | string[];
}

interface Props {
  communities: Community[];
  width?: number;
  height?: number;
}

const PALETTE = [
  '#2A7B9B', // accent-blue
  '#7B6DAA', // accent-purple
  '#2D8B55', // accent-teal
  '#D4A843', // accent-amber
  '#D94F30', // accent-main/vermillion
  '#22c55e', 
  '#f97316', 
  '#06b6d4'
];

export default function ClusterVisualizer({ communities, width, height = 500 }: Props) {
  const graphData = useMemo(() => {
    const nodes: any[] = [];
    const links: any[] = [];

    communities.forEach((c, i) => {
      const color = PALETTE[i % PALETTE.length];
      const communityId = `cluster_${c.id}`;
      
      // Central cluster node
      nodes.push({
        id: communityId,
        name: c.title || `Cluster ${c.id}`,
        val: 5, // make it significantly larger
        color,
        isCluster: true,
      });

      // Parse entities
      let entities: string[] = [];
      if (Array.isArray(c.nodes)) entities = c.nodes;
      else {
        try { entities = JSON.parse(c.nodes || '[]'); } catch { entities = []; }
      }

      // Add entity nodes and link to cluster
      entities.slice(0, 15).forEach(entity => {
        // avoid pure duplicates, though in different clusters it might map multiple times
        const entityId = `entity_${entity}`;
        if (!nodes.find(n => n.id === entityId)) {
          nodes.push({
            id: entityId,
            name: entity,
            val: 1.5,
            color: '#6B6560', // text-secondary
            isCluster: false,
          });
        }
        
        links.push({
          source: communityId,
          target: entityId,
          color: `${color}80` // semi-transparent link
        });
      });
    });

    return { nodes, links };
  }, [communities]);

  return (
    <div style={{ background: 'var(--bg-panel)', width: '100%', height: '100%', position: 'relative' }}>
      <ForceGraph2D
        width={width}
        height={height}
        graphData={graphData}
        nodeColor={(node: any) => node.color}
        linkColor={(link: any) => link.color}
        linkWidth={1}
        nodeRelSize={4}
        onNodeClick={(node: any) => {
          console.log(node);
        }}
        nodeCanvasObject={(node: any, ctx: any, globalScale: any) => {
          const label = node.name;
          const fontSize = node.isCluster ? 14 / globalScale : 10 / globalScale;
          ctx.font = `${node.isCluster ? '600' : '400'} ${fontSize}px "DM Sans", sans-serif`;
          
          if (globalScale > 1 || node.isCluster) {
             const textWidth = ctx.measureText(label).width;
             const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.4); 
             
             ctx.beginPath();
             ctx.arc(node.x, node.y, node.val * 2, 0, 2 * Math.PI, false);
             ctx.fillStyle = node.color;
             ctx.fill();

             // Label block
             ctx.fillStyle = node.isCluster ? 'rgba(250, 247, 242, 0.9)' : 'rgba(253, 249, 243, 0.7)'; // warm editorial backgrounds
             ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + (node.val * 2) + 1, bckgDimensions[0], bckgDimensions[1]);

             // Label text
             ctx.textAlign = 'center';
             ctx.textBaseline = 'middle';
             ctx.fillStyle = node.isCluster ? node.color : '#2C2A28';
             ctx.fillText(label, node.x, node.y + (node.val * 2) + 1 + bckgDimensions[1]/2);
          } else {
             ctx.beginPath();
             ctx.arc(node.x, node.y, node.val * 2, 0, 2 * Math.PI, false);
             ctx.fillStyle = node.color;
             ctx.fill();
          }
        }}
      />
    </div>
  );
}
