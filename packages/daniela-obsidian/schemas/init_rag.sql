CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS public.obsidian_embeddings (
    id BIGSERIAL PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS obsidian_embedding_hnsw_idx 
ON public.obsidian_embeddings 
USING hnsw (embedding vector_cosine_ops);

CREATE OR REPLACE FUNCTION match_obsidian_notes (
    query_embedding VECTOR(384),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (
    id BIGINT,
    file_name TEXT,
    file_path TEXT,
    content TEXT,
    similarity FLOAT
)
LANGUAGE sql STABLE
AS $func$
    SELECT
        id,
        file_name,
        file_path,
        content,
        1 - (obsidian_embeddings.embedding <=> query_embedding) AS similarity
    FROM obsidian_embeddings
    WHERE 1 - (obsidian_embeddings.embedding <=> query_embedding) > match_threshold
    ORDER BY obsidian_embeddings.embedding <=> query_embedding
    LIMIT match_count;
$func$$;
