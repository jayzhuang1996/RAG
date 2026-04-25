'use client';

import { useMemo } from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

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
  '#2A7B9B', '#7B6DAA', '#2D8B55', '#D4A843', '#D94F30', '#22c55e', '#f97316', '#06b6d4'
];

const CustomizedContent = (props: any) => {
  const { root, depth, x, y, width, height, index, payload, colors, rank, name } = props;

  // Don't render text if the box is too small to be readable
  const isLargeEnough = width > 80 && height > 40;
  
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: depth < 2 ? colors[Math.floor((index / root.children.length) * 6)] : 'rgba(255,255,255,0)',
          stroke: '#FDF9F3',
          strokeWidth: depth === 1 ? 2 : 1,
          strokeOpacity: depth === 1 ? 1 : 0.4,
        }}
        // Slight interaction
        onMouseOver={(e: any) => e.target.style.opacity = 0.9}
        onMouseOut={(e: any) => e.target.style.opacity = 1}
      />
      {depth === 1 && isLargeEnough ? (
        <>
          <text 
            x={x + 12} 
            y={y + 24} 
            fill="#ffffff" 
            fontSize={14} 
            fontWeight={600} 
            fontFamily="var(--font-display)"
            pointerEvents="none"
          >
            {name.length > 20 ? name.substring(0, 20) + '...' : name}
          </text>
        </>
      ) : null}
      {depth === 2 && width > 40 && height > 24 ? (
        <text 
          x={x + 8} 
          y={y + 16} 
          fill="rgba(255,255,255,0.9)" 
          fontSize={11} 
          fontFamily="var(--font-mono)"
          pointerEvents="none"
        >
          {name.length > 15 ? name.substring(0, 12) + '..' : name}
        </text>
      ) : null}
    </g>
  );
};

export default function ClusterVisualizer({ communities, width, height = 500 }: Props) {
  const data = useMemo(() => {
    // Only visualize the top 8 macro clusters to prevent visual clutter
    const formattedData = communities.slice(0, 8).map((c, i) => {
      let entities: string[] = [];
      if (Array.isArray(c.nodes)) entities = c.nodes;
      else {
        try { entities = JSON.parse(c.nodes || '[]'); } catch { entities = []; }
      }
      
      const children = entities.slice(0, 5).map(e => ({
        name: e,
        size: 15 + Math.random() * 10 
      }));

      return {
        name: c.title || `Cluster ${c.id}`,
        children: children.length > 0 ? children : [{ name: 'Empty', size: 10 }]
      };
    });

    return [
      {
        name: 'Knowledge Map',
        children: formattedData
      }
    ];
  }, [communities]);

  return (
    <div style={{ background: 'var(--bg-panel)', width: '100%', height: '100%', position: 'relative' }}>
      <ResponsiveContainer width="100%" height={height}>
        <Treemap
          data={data}
          dataKey="size"
          stroke="#fff"
          fill="#D94F30"
          content={<CustomizedContent colors={PALETTE} />}
        >
          <Tooltip 
            contentStyle={{ borderRadius: '8px', border: 'none', background: 'var(--bg-card)', boxShadow: 'var(--shadow-md)', fontFamily: 'var(--font-display)', color: 'var(--text-primary)' }}
            itemStyle={{ color: 'var(--accent-main)' }}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
}
