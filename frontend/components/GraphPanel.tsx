'use client';

import { X, Share2 } from 'lucide-react';

interface Triple {
  subject: string;
  verb: string;
  object: string;
}

interface Props {
  triples: Triple[];
  onClose: () => void;
}

const VERB_COLORS: Record<string, string> = {
  founded: '#f59e0b',
  co_founded: '#f59e0b',
  works_at: '#4f8ef7',
  advises: '#2dd4bf',
  advocates_for: '#9b6dff',
  warns_against: '#ef4444',
  criticizes: '#ef4444',
  disagrees_with: '#f97316',
  collaborated_with: '#22c55e',
  researches: '#06b6d4',
  mentors: '#8b5cf6',
  left: '#94a3b8',
  primarily_covers: '#4f8ef7',
  briefly_mentions: '#64748b',
};

export default function GraphPanel({ triples, onClose }: Props) {
  // Group by subject
  const grouped: Record<string, Triple[]> = {};
  triples.forEach(t => {
    if (!grouped[t.subject]) grouped[t.subject] = [];
    grouped[t.subject].push(t);
  });

  const entities = Object.keys(grouped);

  return (
    <div style={{
      height: '100%',
      background: 'var(--bg-panel)',
      border: '1px solid var(--border)',
      borderRadius: '16px',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        <Share2 size={16} color="var(--accent-purple)" />
        <span style={{ fontWeight: 600, fontSize: '14px', flex: 1 }}>
          Knowledge Graph
        </span>
        <span style={{
          background: 'var(--accent-purple-dim)',
          color: 'var(--accent-purple)',
          border: '1px solid var(--accent-purple)',
          borderRadius: '12px',
          padding: '2px 10px',
          fontSize: '11px',
          fontWeight: 600,
        }}>
          {triples.length} edges
        </span>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '6px',
            display: 'flex',
          }}
        >
          <X size={15} color="var(--text-muted)" />
        </button>
      </div>

      {/* Triples list */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}>
        {entities.map(entity => (
          <div key={entity}>
            {/* Entity header */}
            <div style={{
              fontSize: '13px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginBottom: '8px',
              padding: '6px 10px',
              background: 'var(--bg-card)',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              {entity}
            </div>

            {/* Relationships */}
            <div style={{ paddingLeft: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {grouped[entity].map((t, i) => {
                const verbColor = VERB_COLORS[t.verb] || '#8a8a9a';
                return (
                  <div key={i} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '12px',
                  }}>
                    <div style={{
                      width: '4px',
                      height: '4px',
                      borderRadius: '50%',
                      background: verbColor,
                      flexShrink: 0,
                    }} />
                    <span style={{
                      background: `${verbColor}20`,
                      border: `1px solid ${verbColor}50`,
                      color: verbColor,
                      borderRadius: '4px',
                      padding: '1px 6px',
                      fontSize: '10px',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      flexShrink: 0,
                    }}>
                      {t.verb.replace(/_/g, ' ')}
                    </span>
                    <span style={{ color: 'var(--text-secondary)', flexShrink: 1, minWidth: 0 }}>
                      {t.object}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--border)',
        fontSize: '11px',
        color: 'var(--text-muted)',
        textAlign: 'center',
      }}>
        Extracted from podcast transcripts via Moonshot AI
      </div>
    </div>
  );
}
