import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Podcast Intelligence — GraphRAG Dashboard",
  description: "Multi-agent intelligence platform for podcast knowledge graphs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ background: 'var(--bg-base)', minHeight: '100vh' }}>
        {children}
      </body>
    </html>
  );
}
