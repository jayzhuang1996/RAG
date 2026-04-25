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
          strokeWidth: 2 / (depth + 1e-10),
          strokeOpacity: 1,
        }}
      />
      {depth === 1 && width > 40 && height > 30 ? (
        <text x={x + 8} y={y + 18} fill="#fff" fontSize={14} fontWeight={600} fontFamily="var(--font-display)">
          {name}
        </text>
      ) : null}
      {depth === 2 && width > 30 && height > 20 ? (
        <text x={x + 4} y={y + 12} fill="rgba(255,255,255,0.9)" fontSize={10} fontFamily="var(--font-mono)">
          {name}
        </text>
      ) : null}
    </g>
  );
};

export default function ClusterVisualizer({ communities, width, height = 500 }: Props) {
  const data = useMemo(() => {
    const formattedData = communities.map((c, i) => {
      let entities: string[] = [];
      if (Array.isArray(c.nodes)) entities = c.nodes;
      else {
        try { entities = JSON.parse(c.nodes || '[]'); } catch { entities = []; }
      }
      
      const children = entities.slice(0, 15).map(e => ({
        name: e,
        size: 10 + Math.random() * 20 // Arbitrary size for visual variance
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
