'use client';

import { useEffect, useState } from 'react';
import { Layers, Sparkles, BrainCircuit } from 'lucide-react';
import StrategicInsightCard from './StrategicInsightCard';

interface Community {
  id: number;
  title: string;
  summary: string;
  nodes: string | string[];
}

export default function CommunityExplorer() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/communities')
      .then(r => r.json())
      .then(d => {
        setCommunities(d.communities || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '40px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {[...Array(3)].map((_, i) => (
          <div key={i} className="shimmer" style={{ height: '350px', borderRadius: '24px' }} />
        ))}
      </div>
    );
  }

  if (communities.length === 0) {
    return (
      <div style={{ padding: '80px 40px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <Layers size={48} style={{ marginBottom: '16px', opacity: 0.2 }} />
        <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>No Analysis Found</h3>
        <p style={{ fontSize: '14px', marginTop: '8px' }}>
          Extraction pipeline must be run to generate strategic thematic clusters.
        </p>
      </div>
    );
  }

  return (
    <div style={{ padding: '40px', display: 'flex', flexDirection: 'column', gap: '40px' }}>
      {/* Editorial Header */}
      <div style={{ marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-main)', marginBottom: '8px' }}>
          <BrainCircuit size={20} />
          <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Thematic Intelligence Mapping
          </span>
        </div>
        <h2 style={{ 
          fontSize: '32px', 
          fontWeight: 800, 
          color: 'var(--text-primary)', 
          fontFamily: 'var(--font-display)',
          maxWidth: '600px'
        }}>
          Macro Trends & Strategic Clusters
        </h2>
        <p style={{ 
          fontSize: '16px', 
          color: 'var(--text-muted)', 
          marginTop: '12px',
          maxWidth: '700px',
          lineHeight: 1.6
        }}>
          Using graph-theoretic modularity and semantic analysis, we have distilled 22,000+ conversation triples into 12 actionable strategic domains. 
        </p>
      </div>

      {/* Strategic Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr',
        gap: '32px' 
      }}>
        {communities.map((c, i) => (
          <StrategicInsightCard key={c.id} community={c} index={i} />
        ))}
      </div>

      {/* Footer Insight */}
      <div style={{ 
        marginTop: '40px', 
        padding: '32px', 
        background: 'var(--bg-panel)', 
        borderRadius: '24px',
        textAlign: 'center',
        border: '1px dashed var(--border)'
      }}>
        <Sparkles size={24} color="var(--accent-main)" style={{ marginBottom: '12px', opacity: 0.5 }} />
        <p style={{ fontSize: '14px', color: 'var(--text-muted)', maxWidth: '500px', margin: '0 auto' }}>
          These clusters are dynamically generated. As more episodes are ingested, themes will merge and evolve to reflect the shifting landscape of discussed topics.
        </p>
      </div>
    </div>
  );
}
