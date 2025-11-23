-- Phase 7: Unified Optimization Schema
-- Purpose: Tables for storing AI-generated optimization suggestions
-- Created: 2024-11-18

-- Title Suggestions Table
CREATE TABLE IF NOT EXISTS title_suggestions (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- Title variants (3-part structure)
    title_variants JSONB NOT NULL DEFAULT '[]',
    seo_title_suggestions JSONB DEFAULT NULL,  -- Phase 9 addition

    -- Generation metadata
    generation_model VARCHAR(50),
    generation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generation_cost_usd NUMERIC(10, 6),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_article_title_suggestions UNIQUE(article_id)
);

-- SEO Suggestions Table
CREATE TABLE IF NOT EXISTS seo_suggestions (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- Keywords
    focus_keyword VARCHAR(100),
    primary_keywords JSONB NOT NULL DEFAULT '[]',
    secondary_keywords JSONB NOT NULL DEFAULT '[]',

    -- Meta descriptions
    meta_descriptions JSONB NOT NULL DEFAULT '[]',

    -- Tags
    tags JSONB NOT NULL DEFAULT '[]',

    -- Generation metadata
    generation_model VARCHAR(50),
    generation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generation_cost_usd NUMERIC(10, 6),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_article_seo_suggestions UNIQUE(article_id)
);

-- Article FAQs Table
CREATE TABLE IF NOT EXISTS article_faqs (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- FAQ content
    position INTEGER NOT NULL DEFAULT 0,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    schema_type VARCHAR(50) DEFAULT 'FAQPage',

    -- Generation metadata
    generation_model VARCHAR(50),
    generation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_article_faq_position UNIQUE(article_id, position)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_title_suggestions_article_id ON title_suggestions(article_id);
CREATE INDEX IF NOT EXISTS idx_seo_suggestions_article_id ON seo_suggestions(article_id);
CREATE INDEX IF NOT EXISTS idx_article_faqs_article_id ON article_faqs(article_id);
CREATE INDEX IF NOT EXISTS idx_article_faqs_position ON article_faqs(article_id, position);

-- Add unified_optimization_generated flag to articles table
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS unified_optimization_generated BOOLEAN DEFAULT FALSE;

-- Create index on the flag
CREATE INDEX IF NOT EXISTS idx_articles_unified_optimization_generated
ON articles(unified_optimization_generated)
WHERE unified_optimization_generated = FALSE;

-- Update triggers for timestamp maintenance
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_title_suggestions_updated_at
BEFORE UPDATE ON title_suggestions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seo_suggestions_updated_at
BEFORE UPDATE ON seo_suggestions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_article_faqs_updated_at
BEFORE UPDATE ON article_faqs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Verification query
SELECT
    'title_suggestions' as table_name,
    COUNT(*) as row_count
FROM title_suggestions
UNION ALL
SELECT
    'seo_suggestions',
    COUNT(*)
FROM seo_suggestions
UNION ALL
SELECT
    'article_faqs',
    COUNT(*)
FROM article_faqs;