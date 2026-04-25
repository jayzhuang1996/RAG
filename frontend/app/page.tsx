'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { MessageSquare, Layers, BarChart2, Github } from 'lucide-react';

const ChatInterface = dynamic(() => import('../components/ChatInterface'), { ssr: false });
const CommunityExplorer = dynamic(() => import('../components/CommunityExplorer'), { ssr: false });

const NAV = [
  { id: 'chat', label: 'Intelligence Chat', icon: MessageSquare },
  { id: 'communities', label: 'Knowledge Clusters', icon: Layers },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      overflow: 'hidden',
    }}>
      {/* Sidebar */}
      <aside style={{
        width: '240px',
        flexShrink: 0,
        background: 'transparent',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 16px',
      }}>
        {/* Logo */}
        <div style={{ marginBottom: '32px', padding: '0 8px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            marginBottom: '4px',
          }}>
            <div style={{
              width: '36px',
              height: '36px',
              background: 'var(--accent-main)',
              color: 'white',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '18px',
              boxShadow: 'var(--shadow-sm)'
            }}>
              ⚡
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '15px', fontFamily: 'var(--font-display)' }}>PodcastRAG</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Intelligence Platform</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`nav-item${activeTab === id ? ' active' : ''}`}
              style={{ border: 'none', width: '100%', textAlign: 'left' }}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px',
            borderRadius: '8px',
            background: 'var(--bg-panel)',
            border: '1px solid var(--border)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div className="pulse-dot" />
            <div>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-primary)' }}>API Online</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Railway · FastAPI</div>
            </div>
          </div>

          <div style={{
            marginTop: '16px',
            fontSize: '11px',
            color: 'var(--text-muted)',
            lineHeight: '1.6',
            padding: '0 8px',
          }}>
            <div>LangGraph · BM25 + Vector</div>
            <div>Cohere Rerank · Moonshot AI</div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        minWidth: 0,
        background: 'var(--bg-panel)'
      }}>
        {/* Top bar */}
        <div style={{
          height: '64px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 32px',
          gap: '12px',
          flexShrink: 0,
          background: 'var(--bg-panel)',
        }}>
          <div style={{ flexShrink: 0 }}>
            {activeTab === 'chat' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MessageSquare size={16} color="var(--accent-main)" />
                <span style={{ fontSize: '16px', fontWeight: 600, fontFamily: 'var(--font-display)' }}>Intelligence Chat</span>
              </div>
            )}
            {activeTab === 'communities' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={16} color="var(--accent-main)" />
                <span style={{ fontSize: '16px', fontWeight: 600, fontFamily: 'var(--font-display)' }}>Knowledge Clusters</span>
              </div>
            )}
          </div>

          <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span style={{
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              background: 'var(--accent-light)',
              color: 'var(--accent-main)',
              border: '1px solid var(--accent-muted)',
              borderRadius: '20px',
              padding: '4px 12px',
              fontWeight: 600,
            }}>
              Turbo Synthesis Pipeline
            </span>
            <span style={{
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              background: 'var(--bg-hover)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border)',
              borderRadius: '20px',
              padding: '4px 12px',
            }}>
              Phase 13
            </span>
          </div>
        </div>

        {/* Content area */}
        <div style={{
          flex: 1,
          overflow: 'hidden',
          padding: '24px 32px',
        }}>
          {activeTab === 'chat' && (
            <div style={{ height: '100%', maxWidth: '1000px', margin: '0 auto' }}>
              <ChatInterface />
            </div>
          )}
          {activeTab === 'communities' && (
            <div style={{
              height: '100%',
              maxWidth: '1000px',
              margin: '0 auto',
              background: 'var(--bg-panel)',
              border: '1px solid var(--border)',
              borderRadius: '16px',
              boxShadow: 'var(--shadow-md)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}>
              <div style={{
                padding: '24px 32px',
                borderBottom: '1px solid var(--border)',
                background: 'var(--bg-card)',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}>
                <Layers size={18} color="var(--accent-main)" />
                <span style={{ fontWeight: 600, fontSize: '16px', fontFamily: 'var(--font-display)' }}>Knowledge Clusters</span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: 'auto', fontFamily: 'var(--font-mono)' }}>
                  Greedy Modularity · networkx
                </span>
              </div>
              <div style={{ flex: 1, overflowY: 'auto' }}>
                <CommunityExplorer />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
