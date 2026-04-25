'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Sparkles, BookOpen, AlertCircle } from 'lucide-react';
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState('');
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
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/chat`, {
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
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: 'error',
        content: err.message,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div style={{ display: 'flex', height: '100%', width: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0 }}>
        {/* Messages area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>
          {messages.length === 0 && (
            <div style={{ 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              gap: '24px',
              paddingBottom: '60px'
            }}>
              <div style={{ textAlign: 'center' }}>
                <Sparkles size={48} color="var(--accent-main)" style={{ marginBottom: '16px', opacity: 0.8 }} />
                <h2 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
                  Intelligence Chat
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '14px', maxWidth: '400px', margin: '8px auto' }}>
                  Analyze thematic clusters and relationship graphs across the transcript database.
                </p>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', maxWidth: '600px' }}>
                {SUGGESTED.map((s, i) => (
                  <button 
                    key={i} 
                    className="suggestion-chip"
                    onClick={() => { setQuery(s); handleSubmit(s); }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', maxWidth: '850px', margin: '0 auto' }}>
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`} style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                gap: '8px'
              }}>
                <div style={{
                  padding: msg.role === 'error' ? '16px' : '0',
                  background: msg.role === 'user' ? 'var(--accent-main)' : (msg.role === 'error' ? 'var(--accent-main-dim)' : 'transparent'),
                  color: msg.role === 'user' ? '#fff' : (msg.role === 'error' ? 'var(--accent-main)' : 'var(--text-secondary)'),
                  borderRadius: '16px',
                  border: msg.role === 'error' ? '1px solid var(--accent-main)' : 'none',
                  fontSize: '15px',
                  lineHeight: '1.7',
                  width: msg.role === 'user' ? 'auto' : '100%',
                  maxWidth: msg.role === 'user' ? '80%' : '100%',
                }}>
                  {msg.role === 'user' ? (
                    <div style={{ padding: '12px 20px' }}>{msg.content}</div>
                  ) : (
                    <div className="prose-editorial">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                  )}

                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
                      <p style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '12px' }}>
                        Sources
                      </p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {msg.sources.map((s, idx) => (
                          <button
                            key={idx} 
                            onClick={(e) => {
                              e.preventDefault();
                              const text = s.text || "Transcript chunk context missing.";
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
                          >
                            <BookOpen size={10} />
                            [{s.index}] {s.title}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

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
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{ padding: '16px' }}>
                  <div className="shimmer" style={{ width: '120px', height: '24px', borderRadius: '4px' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input box */}
        <div style={{ 
          padding: '24px 32px', 
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-panel)'
        }}>
          <form 
            onSubmit={e => { e.preventDefault(); handleSubmit(); }}
            style={{ display: 'flex', gap: '12px', maxWidth: '850px', margin: '0 auto' }}
          >
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Ask anything about the podcast database..."
              disabled={loading}
              className="chat-input"
              style={{
                flex: 1,
                background: 'var(--bg-panel)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                padding: '14px 20px',
                color: 'var(--text-primary)',
                fontSize: '15px',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="send-button"
              style={{
                background: query.trim() ? 'var(--accent-main)' : 'var(--bg-panel)',
                border: `1px solid ${query.trim() ? 'var(--accent-main)' : 'var(--border)'}`,
                borderRadius: '12px',
                padding: '0 20px',
                cursor: query.trim() ? 'pointer' : 'default',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Send size={18} color={query.trim() ? '#fff' : 'var(--text-muted)'} />
            </button>
          </form>
        </div>
      </div>

      {/* Pop-up transcript overlay */}
      {selectedSource && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(10, 8, 5, 0.4)',
          backdropFilter: 'blur(2px)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px'
        }}>
          <div style={{
            background: 'var(--bg-panel)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            width: '100%',
            maxWidth: '600px',
            maxHeight: '80%',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 20px 40px rgba(0,0,0,0.1)'
          }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 600, fontSize: '14px', fontFamily: 'var(--font-display)' }}>
                [Source {selectedSource.index}] {selectedSource.title}
              </span>
              <button 
                onClick={() => setSelectedSource(null)} 
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  cursor: 'pointer', 
                  fontSize: '24px',
                  color: 'var(--text-muted)',
                  lineHeight: 1
                }}
              >
                &times;
              </button>
            </div>
            <div style={{ padding: '24px', overflowY: 'auto', fontSize: '14px', lineHeight: '1.7', color: 'var(--text-secondary)' }}>
              {selectedSource.text}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
