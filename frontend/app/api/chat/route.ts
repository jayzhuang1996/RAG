import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function POST(req: NextRequest) {
    try {
        const { query } = await req.json();

        // 1. Get embedding (Using a simplified approach for the MVP: 
        // In a pro setup, we'd use OpenAI or Moonshot embeddings. 
        // Here we'll simulate or use a server-side model if available.)

        // For now, let's just fetch the top matching text using keyword search on Supabase 
        // until we have the vector RPC function set up.

        const { data: results, error } = await supabase
            .from('viking_chunks')
            .select('text, video_id, type')
            .ilike('text', `%${query}%`)
            .eq('type', 'parent')
            .limit(5);

        if (error) throw error;

        const context = results.map((r, i) => `[Source ${i + 1}]\n${r.text}`).join('\n\n---\n\n');

        // 2. Call Moonshot AI
        const response = await fetch('https://api.moonshot.ai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.MOONSHOT_API_KEY}`
            },
            body: JSON.stringify({
                model: 'moonshot-v1-8k',
                messages: [
                    { role: 'system', content: 'Answer based ONLY on the context. Cite as [Source N].' },
                    { role: 'user', content: `Context:\n${context}\n\nQuestion: ${query}` }
                ],
                temperature: 0.3,
            })
        });

        const data = await response.json();
        return NextResponse.json({
            answer: data.choices[0].message.content,
            sources: results.map(r => ({ title: "Podcast Episode", id: r.video_id }))
        });

    } catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
