'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Loader2, Mic, Zap, BookOpen } from 'lucide-react';
import GraphPanel from './GraphPanel';

interface Message {
  role: 'user' | 'assistant' | 'error';
  content: string;
  sources?: { index: number; video_id: string; title: string }[];
  graph_data?: { subject: string; verb: string; object: string }[];
}

const SUGGESTED = [
  "What are the most discussed AI trends across all episodes?",
  "Who are the key figures in AI safety and what do they believe?",
  "What startups have been mentioned most frequently?",
  "Summarize the recurring themes around AGI timelines",
];

export default function ChatInterface() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeGraph, setActiveGraph] = useState<Message | null>(null);

  const handleSubmit = async (q?: string) => {
    const question = q || query;
    if (!question.trim()) return;

    const userMsg: Message = { role: 'user', content: question };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: question }),
      });
      const data = await res.json();

      if (data.error) throw new Error(data.error);

      const assistantMsg: Message = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        graph_data: data.graph_data,
      };
      setMessages(prev => [...prev, assistantMsg]);
      if (data.graph_data?.length > 0) setActiveGraph(assistantMsg);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: 'error',
        content: `Error: ${err.message || 'Failed to get a response. Is the API running?'}`,
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', gap: '20px', height: '100%' }}>
      {/* Chat Column */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0,
        background: 'var(--bg-panel)',
        borderRadius: '16px',
        border: '1px solid var(--border)',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <Zap size={18} color="var(--accent-blue)" />
          <span style={{ fontWeight: 600, fontSize: '15px' }}>Podcast Intelligence</span>
          <span style={{ marginLeft: 'auto', fontSize: '12px', color: 'var(--text-muted)' }}>
            LangGraph · BM25 + Vector · Cohere Rerank
          </span>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}>
          {messages.length === 0 && (
            <div style={{ marginTop: '40px' }}>
              <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginBottom: '32px', fontSize: '14px' }}>
                Ask anything about your podcast knowledge base
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {SUGGESTED.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => handleSubmit(s)}
                    style={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border)',
                      borderRadius: '10px',
                      padding: '14px 16px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      color: 'var(--text-secondary)',
                      fontSize: '13px',
                      lineHeight: '1.5',
                      transition: 'all 0.15s',
                    }}
                    onMouseOver={e => (e.currentTarget.style.borderColor = 'var(--accent-blue)')}
                    onMouseOut={e => (e.currentTarget.style.borderColor = 'var(--border)')}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}>
              {msg.role === 'user' ? (
                <div style={{
                  maxWidth: '75%',
                  background: 'var(--accent-blue)',
                  borderRadius: '16px 16px 4px 16px',
                  padding: '12px 18px',
                  color: '#fff',
                  fontSize: '14px',
                  lineHeight: '1.6',
                }}>
                  {msg.content}
                </div>
              ) : msg.role === 'error' ? (
                <div style={{
                  maxWidth: '85%',
                  background: '#2a1010',
                  border: '1px solid #5a2020',
                  borderRadius: '4px 16px 16px 16px',
                  padding: '14px 18px',
                  color: '#ff6b6b',
                  fontSize: '13px',
                }}>
                  {msg.content}
                </div>
              ) : (
                <div style={{
                  maxWidth: '100%',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: '4px 16px 16px 16px',
                  padding: '18px 22px',
                }}>
                  <div className="prose-dark">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border)' }}>
                      <p style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
                        Sources
                      </p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {msg.sources.map((s, idx) => (
                          <span key={idx} className="source-pill">
                            <BookOpen size={10} />
                            [{s.index}] {s.title}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Graph toggle */}
                  {msg.graph_data && msg.graph_data.length > 0 && (
                    <button
                      onClick={() => setActiveGraph(activeGraph === msg ? null : msg)}
                      style={{
                        marginTop: '12px',
                        background: activeGraph === msg ? 'var(--accent-purple-dim)' : 'var(--bg-hover)',
                        border: `1px solid ${activeGraph === msg ? 'var(--accent-purple)' : 'var(--border)'}`,
                        borderRadius: '8px',
                        padding: '6px 14px',
                        fontSize: '12px',
                        color: activeGraph === msg ? 'var(--accent-purple)' : 'var(--text-secondary)',
                        cursor: 'pointer',
                        transition: 'all 0.15s',
                      }}
                    >
                      {msg.graph_data.length} relationships — {activeGraph === msg ? 'Hide' : 'Show'} graph →
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '4px 16px 16px 16px',
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                color: 'var(--text-secondary)',
                fontSize: '13px',
              }}>
                <Loader2 size={16} className="animate-spin" color="var(--accent-blue)" style={{ animation: 'spin 1s linear infinite' }} />
                <span>Researcher → Analyst → Writer...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
          <form
            onSubmit={e => { e.preventDefault(); handleSubmit(); }}
            style={{ display: 'flex', gap: '10px', alignItems: 'center' }}
          >
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Ask about your podcasts..."
              disabled={loading}
              style={{
                flex: 1,
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                padding: '13px 18px',
                color: 'var(--text-primary)',
                fontSize: '14px',
                outline: 'none',
                transition: 'border-color 0.15s',
              }}
              onFocus={e => (e.target.style.borderColor = 'var(--accent-blue)')}
              onBlur={e => (e.target.style.borderColor = 'var(--border)')}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              style={{
                background: query.trim() ? 'var(--accent-blue)' : 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                padding: '13px 18px',
                cursor: query.trim() ? 'pointer' : 'default',
                display: 'flex',
                alignItems: 'center',
                transition: 'all 0.15s',
              }}
            >
              <Send size={16} color={query.trim() ? '#fff' : 'var(--text-muted)'} />
            </button>
          </form>
        </div>
      </div>

      {/* Graph Panel (conditionally shown) */}
      {activeGraph && activeGraph.graph_data && (
        <div style={{ width: '350px', flexShrink: 0 }}>
          <GraphPanel
            triples={activeGraph.graph_data}
            onClose={() => setActiveGraph(null)}
          />
        </div>
      )}
    </div>
  );
}
