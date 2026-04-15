'use client';

import { useEffect, useState } from 'react';
import { Layers, ChevronDown, ChevronRight, Users } from 'lucide-react';

interface Community {
  id: number;
  title: string;
  summary: string;
  nodes: string | string[];
}

export default function CommunityExplorer() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    fetch('/api/communities')
      .then(r => r.json())
      .then(d => {
        setCommunities(d.communities || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const getNodes = (c: Community): string[] => {
    if (Array.isArray(c.nodes)) return c.nodes;
    try { return JSON.parse(c.nodes || '[]'); } catch { return []; }
  };

  const PALETTE = [
    'var(--accent-blue)', 'var(--accent-purple)', 'var(--accent-teal)',
    'var(--accent-amber)', '#22c55e', '#f97316', '#06b6d4', '#ec4899',
  ];

  if (loading) {
    return (
      <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {[...Array(6)].map((_, i) => (
          <div key={i} className="shimmer" style={{ height: '72px', borderRadius: '10px' }} />
        ))}
      </div>
    );
  }

  if (communities.length === 0) {
    return (
      <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <Layers size={32} style={{ marginBottom: '12px', opacity: 0.4 }} />
        <p style={{ fontSize: '14px' }}>No communities found.</p>
        <p style={{ fontSize: '12px', marginTop: '8px' }}>
          Run <code style={{ color: 'var(--accent-teal)' }}>python main.py communities</code> to generate them.
        </p>
      </div>
    );
  }

  return (
    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
        {communities.length} thematic clusters extracted via Greedy Modularity
      </p>

      {communities.map((c, i) => {
        const nodes = getNodes(c);
        const color = PALETTE[i % PALETTE.length];
        const isOpen = expanded === c.id;

        return (
          <div key={c.id} className="community-card" onClick={() => setExpanded(isOpen ? null : c.id)}>
            {/* Card header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
              {/* Color dot */}
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: `${color}20`,
                border: `1px solid ${color}60`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                fontSize: '12px',
                fontWeight: 700,
                color,
              }}>
                {i + 1}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{
                  fontSize: '13px',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  marginBottom: '2px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}>
                  {c.title || `Community ${c.id}`}
                </p>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Users size={10} />
                  {nodes.length} entities
                </p>
              </div>

              <div style={{ color: 'var(--text-muted)', flexShrink: 0 }}>
                {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </div>
            </div>

            {/* Expanded detail */}
            {isOpen && (
              <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid var(--border)' }}>
                {c.summary && (
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '12px' }}>
                    {c.summary}
                  </p>
                )}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {nodes.slice(0, 12).map((n: string, ni: number) => (
                    <span key={ni} style={{
                      background: 'var(--bg-base)',
                      border: '1px solid var(--border)',
                      borderRadius: '12px',
                      padding: '2px 10px',
                      fontSize: '11px',
                      color: 'var(--text-secondary)',
                    }}>
                      {n}
                    </span>
                  ))}
                  {nodes.length > 12 && (
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', padding: '2px 6px' }}>
                      +{nodes.length - 12} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
