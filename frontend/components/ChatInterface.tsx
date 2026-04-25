'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Loader2, Mic, Zap, BookOpen } from 'lucide-react';
import MermaidVisualizer from './MermaidVisualizer';

interface Message {
  role: 'user' | 'assistant' | 'error';
  content: string;
  sources?: { index: number; video_id: string; title: string; text?: string }[];
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
  const [selectedSource, setSelectedSource] = useState<{ title: string; text: string; index: number } | null>(null);

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
      
      let data;
      const text = await res.text();
      try {
        data = JSON.parse(text);
      } catch (e) {
        throw new Error(`API Endpoint Error: ${text.substring(0, 100)}...`);
      }

      if (!res.ok || data.error) throw new Error(data.error || 'Unknown error occurred');

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
        content: err.message,
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
          padding: '24px 32px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg-card)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}>
          <Zap size={18} color="var(--accent-main)" />
          <span style={{ fontWeight: 600, fontSize: '16px', fontFamily: 'var(--font-display)' }}>Podcast Intelligence</span>
          <span style={{ marginLeft: 'auto', fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
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
                  background: 'var(--accent-main)',
                  boxShadow: 'var(--shadow-sm)',
                  borderRadius: '16px 16px 4px 16px',
                  padding: '14px 20px',
                  color: '#fff',
                  fontSize: '15px',
                  lineHeight: '1.6',
                }}>
                  {msg.content}
                </div>
              ) : msg.role === 'error' ? (
                <div style={{
                  maxWidth: '85%',
                  background: 'var(--accent-light)',
                  border: '1px solid var(--accent-muted)',
                  borderRadius: '4px 16px 16px 16px',
                  padding: '14px 18px',
                  color: 'var(--accent-hover)',
                  fontSize: '14px',
                  fontFamily: 'var(--font-mono)'
                }}>
                  {msg.content}
                </div>
              ) : (
                <div style={{
                  maxWidth: '100%',
                  background: 'var(--bg-panel)',
                  border: '1px solid var(--border)',
                  boxShadow: 'var(--shadow-md)',
                  borderRadius: '4px 16px 16px 16px',
                  padding: '24px',
                }}>
                  <div className="prose-editorial">
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
                          <button
                            key={idx} 
                            onClick={(e) => {
                              e.preventDefault();
                              const text = s.text || "Transcript chunk not provided by backend.";
                              setSelectedSource({ title: s.title, text, index: s.index });
                            }}
                            className="source-pill"
                            style={{ 
                              textDecoration: 'none', 
                              transition: 'transform 0.15s', 
                              cursor: 'pointer',
                              border: 'none',
                              fontFamily: 'inherit'
                            }}
                            onMouseOver={e => e.currentTarget.style.transform = 'translateY(-1px)'}
                            onMouseOut={e => e.currentTarget.style.transform = 'none'}
                          >
                            <BookOpen size={10} />
                            [{s.index}] {s.title}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Graph toggle */}
                  {msg.graph_data && msg.graph_data.length > 0 && (
                    <div style={{ marginTop: '16px' }}>
                      <button
                        onClick={() => setActiveGraph(activeGraph === msg ? null : msg)}
                        style={{
                          background: 'var(--bg-card)',
                          color: 'var(--accent-main)',
                          border: '1px solid var(--accent-main)',
                          padding: '6px 12px',
                          borderRadius: '8px',
                          fontSize: '11px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          marginBottom: activeGraph === msg ? '12px' : '0'
                        }}
                      >
                        {activeGraph === msg ? 'Hide Structural Map' : 'View Structural Map'}
                      </button>
                      
                      {activeGraph === msg && (
                        <div style={{ 
                          height: '350px', 
                          border: '1px solid var(--border)', 
                          borderRadius: '12px', 
                          overflow: 'hidden' 
                        }}>
                          <MermaidVisualizer triples={msg.graph_data} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                background: 'var(--bg-panel)',
                border: '1px solid var(--border)',
                boxShadow: 'var(--shadow-sm)',
                borderRadius: '4px 16px 16px 16px',
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                color: 'var(--text-secondary)',
                fontSize: '13px',
                fontFamily: 'var(--font-mono)'
              }}>
                <Loader2 size={16} className="animate-spin" color="var(--accent-main)" style={{ animation: 'spin 1s linear infinite' }} />
                <span>Researcher → Analyst → Writer...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div style={{ padding: '20px 24px', borderTop: '1px solid var(--border)', background: 'var(--bg-card)' }}>
          <form
            onSubmit={e => { e.preventDefault(); handleSubmit(); }}
            style={{ display: 'flex', gap: '12px', alignItems: 'center' }}
          >
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Ask about your podcasts..."
              disabled={loading}
              style={{
                flex: 1,
                background: 'var(--bg-panel)',
                border: '1px solid var(--border)',
                boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.02)',
                borderRadius: '12px',
                padding: '14px 20px',
                color: 'var(--text-primary)',
                fontSize: '15px',
                outline: 'none',
                transition: 'border-color 0.15s, box-shadow 0.15s',
              }}
              onFocus={e => { e.target.style.borderColor = 'var(--accent-main)'; e.target.style.boxShadow = '0 0 0 3px var(--accent-light)'; }}
              onBlur={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.boxShadow = 'inset 0 1px 3px rgba(0,0,0,0.02)'; }}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              style={{
                background: query.trim() ? 'var(--accent-main)' : 'var(--bg-panel)',
                border: `1px solid ${query.trim() ? 'var(--accent-main)' : 'var(--border)'}`,
                boxShadow: query.trim() ? 'var(--shadow-sm)' : 'none',
                borderRadius: '12px',
                padding: '14px 20px',
                cursor: query.trim() ? 'pointer' : 'default',
                display: 'flex',
                alignItems: 'center',
                transition: 'all 0.15s',
              }}
            >
              <Send size={18} color={query.trim() ? '#fff' : 'var(--text-muted)'} />
            </button>
          </form>
        </div>
      </div>

    </div>
  );
}
