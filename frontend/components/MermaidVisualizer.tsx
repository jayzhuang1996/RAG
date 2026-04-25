'use client';

import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface Triple {
  subject: string;
  verb: string;
  object: string;
}

export default function MermaidVisualizer({ triples }: { triples: Triple[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        fontFamily: 'var(--font-mono)',
        primaryColor: '#FDF9F3',
        primaryTextColor: '#2C2A28',
        primaryBorderColor: '#D94F30',
        lineColor: '#A8A29E',
        secondaryColor: '#FAF7F2',
        tertiaryColor: '#FFFFFF',
      },
    });

    if (containerRef.current) {
      // Build flowchart syntax
      let graphDefinition = 'flowchart LR\n';
      
      // Clean function to make valid mermaid IDs
      const clean = (s: string) => s.replace(/[^a-zA-Z0-9]/g, '_');
      
      // Keep it minimal and readable (max 12 relationships to avoid giant hairballs)
      const visibleTriples = triples.slice(0, 12);
      
      visibleTriples.forEach(t => {
        const subId = clean(t.subject);
        const objId = clean(t.object);
        const verbStr = t.verb.substring(0, 30).replace(/"/g, "'");
        graphDefinition += `    ${subId}["${t.subject}"] -->|"${verbStr}"| ${objId}["${t.object}"]\n`;
      });

      mermaid.render('mermaid-svg', graphDefinition).then(({ svg }) => {
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      }).catch(e => {
        console.error("Mermaid rendering failed", e);
        if (containerRef.current) containerRef.current.innerHTML = "<p style='color:var(--text-muted);font-size:12px;text-align:center;'>Unable to draw complex relationship map.<br/>Some node labels may contain unsupported characters.</p>";
      });
    }
  }, [triples]);

  return (
    <div 
      style={{ 
        width: '100%', 
        height: '100%', 
        overflow: 'auto', 
        background: 'var(--bg-panel)',
        padding: '24px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}
    >
      <div ref={containerRef} />
    </div>
  );
}
