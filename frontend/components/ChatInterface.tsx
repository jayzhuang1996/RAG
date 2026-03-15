"use client";

import { useState } from 'react';
import { Send, Loader2, Play } from 'lucide-react';

export default function ChatInterface() {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        const userMsg = { role: 'user', content: query };
        setMessages(prev => [...prev, userMsg]);
        setQuery('');
        setLoading(true);

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query }),
            });
            const data = await res.json();
            setMessages(prev => [...prev, { role: 'assistant', content: data.answer, sources: data.sources }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'error', content: 'Failed to find an answer.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full max-w-4xl mx-auto p-4 space-y-4">
            <div className="flex-1 overflow-y-auto space-y-6 pr-4">
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] p-4 rounded-2xl ${msg.role === 'user'
                                ? 'bg-blue-600 text-white shadow-lg'
                                : 'glass shadow-xl'
                            }`}>
                            <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                            {msg.sources && (
                                <div className="mt-4 pt-3 border-t border-white/10 space-y-2">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-blue-400">Sources</p>
                                    {msg.sources.map((s: any, idx: number) => (
                                        <div key={idx} className="flex items-center text-sm text-gray-400 hover:text-white transition-colors cursor-pointer group">
                                            <Play className="w-3 h-3 mr-2 text-blue-500 group-hover:scale-110 transition-transform" />
                                            {s.title}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="glass p-4 rounded-2xl animate-pulse flex items-center">
                            <Loader2 className="w-5 h-5 animate-spin mr-3 text-blue-500" />
                            Thinking...
                        </div>
                    </div>
                )}
            </div>

            <form onSubmit={handleSubmit} className="relative mt-auto">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask about your podcasts..."
                    className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl py-4 pl-6 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-lg shadow-2xl"
                />
                <button
                    disabled={loading}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-3 bg-blue-600 rounded-xl hover:bg-blue-500 transition-all disabled:opacity-50 shadow-lg"
                >
                    <Send className="w-5 h-5 text-white" />
                </button>
            </form>
        </div>
    );
}
