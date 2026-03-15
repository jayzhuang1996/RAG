-- 1. Enable Vector Extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Videos Table
CREATE TABLE IF NOT EXISTS viking_videos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    upload_date TEXT,
    url TEXT,
    status TEXT DEFAULT 'new' CHECK(status IN ('new', 'processed', 'error'))
);

-- 3. Transcripts Table
CREATE TABLE IF NOT EXISTS viking_transcripts (
    video_id TEXT PRIMARY KEY REFERENCES viking_videos(id) ON DELETE CASCADE,
    full_text TEXT,
    raw_json JSONB
);

-- 3.5 Metadata Table (Flat Entities)
CREATE TABLE IF NOT EXISTS viking_metadata (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    video_id TEXT NOT NULL REFERENCES viking_videos(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK(type IN ('guest', 'topic', 'company')),
    value TEXT NOT NULL
);

-- 4. Chunks Table (With Vector Support)
CREATE TABLE IF NOT EXISTS viking_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id TEXT NOT NULL REFERENCES viking_videos(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('parent', 'child')),
    parent_id UUID REFERENCES viking_chunks(id) ON DELETE CASCADE,
    start_time REAL,
    end_time REAL,
    chunk_index INTEGER,
    embedding vector(384) -- Using 384 dimensions for all-MiniLM-L6-v2
);

-- 5. Relationships Table (GraphRAG)
CREATE TABLE IF NOT EXISTS viking_relationships (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    video_id TEXT NOT NULL REFERENCES viking_videos(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    verb TEXT NOT NULL,
    object TEXT NOT NULL
);

-- 6. Indexes for Performance
CREATE INDEX ON viking_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON viking_relationships (subject);
CREATE INDEX ON viking_relationships (object);

-- 7. Vector Search Function (RPC)
CREATE OR REPLACE FUNCTION match_chunks (
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id UUID,
  video_id TEXT,
  text TEXT,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    viking_chunks.id,
    viking_chunks.video_id,
    viking_chunks.text,
    1 - (viking_chunks.embedding <=> query_embedding) AS similarity
  FROM viking_chunks
  WHERE 1 - (viking_chunks.embedding <=> query_embedding) > match_threshold
    AND viking_chunks.type = 'child'
  ORDER BY viking_chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
