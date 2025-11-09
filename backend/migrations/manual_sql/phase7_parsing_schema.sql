-- ============================================================================
-- Phase 7: Article Structured Parsing - Database Schema Design
-- ============================================================================
-- Version: 1.0
-- Date: 2025-11-08
-- Author: CMS Automation Team
--
-- This SQL DDL file defines the database schema extensions required for
-- the Article Structured Parsing feature (Phase 7). This includes:
--
-- 1. Extension of the `articles` table with parsing-specific fields
-- 2. Creation of `article_images` table for image management
-- 3. Creation of `article_image_reviews` table for parsing confirmation workflow
-- 4. Supporting indexes for query performance
-- 5. Triggers for automatic timestamp updates
--
-- NOTE: This is a DESIGN DOCUMENT. Do NOT execute directly.
-- Use Alembic migrations for actual schema changes.
-- ============================================================================

-- ============================================================================
-- 1. ARTICLES TABLE EXTENSIONS
-- ============================================================================
-- Add parsing-related columns to the existing articles table

-- Title decomposition fields (replacing single 'title' field)
ALTER TABLE articles ADD COLUMN title_prefix VARCHAR(200)
    COMMENT 'First part of title (optional), e.g., "【專題報導】"';

ALTER TABLE articles ADD COLUMN title_main VARCHAR(500) NOT NULL DEFAULT ''
    COMMENT 'Main title (required), e.g., "2024年醫療保健創新趨勢"';

ALTER TABLE articles ADD COLUMN title_suffix VARCHAR(200)
    COMMENT 'Subtitle/suffix (optional), e.g., "從AI診斷到遠距醫療"';

-- Author information
ALTER TABLE articles ADD COLUMN author_line VARCHAR(300)
    COMMENT 'Raw author line from document, e.g., "文／張三｜編輯／李四"';

ALTER TABLE articles ADD COLUMN author_name VARCHAR(100)
    COMMENT 'Cleaned author name extracted from author_line, e.g., "張三"';

-- Cleaned body content
ALTER TABLE articles ADD COLUMN body_html TEXT
    COMMENT 'Sanitized body HTML with headers/images/meta removed, ready for publishing';

-- SEO and metadata fields
ALTER TABLE articles ADD COLUMN meta_description TEXT
    COMMENT 'Extracted meta description for SEO (150-160 chars recommended)';

ALTER TABLE articles ADD COLUMN seo_keywords TEXT[]
    COMMENT 'Array of SEO keywords extracted from content';

-- Note: tags TEXT[] already exists in the current schema, reusing for content tags

-- Parsing confirmation workflow
ALTER TABLE articles ADD COLUMN parsing_confirmed BOOLEAN DEFAULT FALSE
    COMMENT 'Whether parsing has been reviewed and confirmed by user (Step 1)';

ALTER TABLE articles ADD COLUMN parsing_confirmed_at TIMESTAMP
    COMMENT 'Timestamp when parsing was confirmed';

ALTER TABLE articles ADD COLUMN parsing_confirmed_by VARCHAR(100)
    COMMENT 'User ID or identifier who confirmed the parsing';

ALTER TABLE articles ADD COLUMN parsing_feedback TEXT
    COMMENT 'User feedback on parsing quality during confirmation';

-- Indexes for parsing queries
CREATE INDEX idx_articles_parsing_confirmed ON articles(parsing_confirmed)
    WHERE parsing_confirmed = FALSE;

CREATE INDEX idx_articles_parsing_confirmed_at ON articles(parsing_confirmed_at DESC);


-- ============================================================================
-- 2. ARTICLE_IMAGES TABLE
-- ============================================================================
-- Stores structured information about images extracted from articles

CREATE TABLE article_images (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign key to articles table
    article_id INTEGER NOT NULL
        REFERENCES articles(id) ON DELETE CASCADE,

    -- Image file paths
    preview_path VARCHAR(500)
        COMMENT 'Path to preview/thumbnail image in storage',

    source_path VARCHAR(500)
        COMMENT 'Path to downloaded high-resolution source image',

    source_url VARCHAR(1000)
        COMMENT 'Original "原圖/點此下載" URL from Google Doc',

    -- Image content
    caption TEXT
        COMMENT 'Image caption extracted from document',

    -- Position in article
    position INTEGER NOT NULL
        COMMENT 'Paragraph index (0-based) where image should appear in body',

    -- Technical specifications (JSONB)
    metadata JSONB
        COMMENT 'Technical image metadata: dimensions, file size, format, EXIF',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT article_images_positive_position CHECK (position >= 0),
    CONSTRAINT article_images_unique_position UNIQUE (article_id, position)
);

-- Indexes
CREATE INDEX idx_article_images_article_id ON article_images(article_id);
CREATE INDEX idx_article_images_position ON article_images(article_id, position);
CREATE INDEX idx_article_images_created_at ON article_images(created_at DESC);

-- GIN index for JSONB metadata queries (optional, for advanced filtering)
CREATE INDEX idx_article_images_metadata_gin ON article_images USING GIN(metadata);

COMMENT ON TABLE article_images IS
    'Stores structured information about images extracted from articles, including source assets and technical specifications';


-- ============================================================================
-- 3. ARTICLE_IMAGE_REVIEWS TABLE
-- ============================================================================
-- Tracks reviewer feedback and actions on individual images during parsing confirmation

CREATE TABLE article_image_reviews (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign key to article_images
    article_image_id INTEGER NOT NULL
        REFERENCES article_images(id) ON DELETE CASCADE,

    -- Optional link to worklist (if worklist system is used)
    worklist_item_id INTEGER
        COMMENT 'Optional FK to worklist_items table',

    -- Review action
    action VARCHAR(20) NOT NULL
        CHECK (action IN ('keep', 'remove', 'replace_caption', 'replace_source'))
        COMMENT 'Action taken: keep|remove|replace_caption|replace_source',

    -- Replacement data (conditional based on action)
    new_caption TEXT
        COMMENT 'Replacement caption if action=replace_caption',

    new_source_url VARCHAR(1000)
        COMMENT 'Replacement source URL if action=replace_source',

    -- Review notes
    reviewer_notes TEXT
        COMMENT 'Notes explaining the review decision or rationale',

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT article_image_reviews_valid_action CHECK (
        action IN ('keep', 'remove', 'replace_caption', 'replace_source')
    ),

    -- If action is 'replace_caption', new_caption must be provided
    CONSTRAINT article_image_reviews_caption_required CHECK (
        action != 'replace_caption' OR new_caption IS NOT NULL
    ),

    -- If action is 'replace_source', new_source_url must be provided
    CONSTRAINT article_image_reviews_source_required CHECK (
        action != 'replace_source' OR new_source_url IS NOT NULL
    )
);

-- Indexes
CREATE INDEX idx_article_image_reviews_article_image ON article_image_reviews(article_image_id);
CREATE INDEX idx_article_image_reviews_worklist_item ON article_image_reviews(worklist_item_id);
CREATE INDEX idx_article_image_reviews_action ON article_image_reviews(action);
CREATE INDEX idx_article_image_reviews_created_at ON article_image_reviews(created_at DESC);

COMMENT ON TABLE article_image_reviews IS
    'Tracks reviewer feedback and actions on individual images during parsing confirmation (Step 1)';


-- ============================================================================
-- 4. TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Ensure the update_updated_at_column() function exists (should be defined in base migration)
-- If not, create it:
/*
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
*/

-- Apply trigger to article_images table
DROP TRIGGER IF EXISTS update_article_images_updated_at ON article_images;
CREATE TRIGGER update_article_images_updated_at
    BEFORE UPDATE ON article_images
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 5. PERFORMANCE OPTIMIZATION QUERIES
-- ============================================================================

-- Query 1: Get all unparsed articles for Worklist "Parsing Confirmation" view
-- Uses idx_articles_parsing_confirmed
/*
SELECT
    a.id,
    a.title_main,
    a.title_prefix,
    a.title_suffix,
    a.author_name,
    a.created_at,
    COUNT(ai.id) as image_count
FROM articles a
LEFT JOIN article_images ai ON a.id = ai.article_id
WHERE a.parsing_confirmed = FALSE
GROUP BY a.id
ORDER BY a.created_at DESC
LIMIT 50;
*/

-- Query 2: Get article with all images for parsing confirmation UI
-- Uses idx_article_images_article_id and idx_article_images_position
/*
SELECT
    a.id,
    a.title_prefix,
    a.title_main,
    a.title_suffix,
    a.author_line,
    a.author_name,
    a.body_html,
    a.meta_description,
    a.seo_keywords,
    a.tags,
    json_agg(
        json_build_object(
            'id', ai.id,
            'position', ai.position,
            'preview_path', ai.preview_path,
            'source_url', ai.source_url,
            'caption', ai.caption,
            'metadata', ai.metadata
        ) ORDER BY ai.position
    ) as images
FROM articles a
LEFT JOIN article_images ai ON a.id = ai.article_id
WHERE a.id = :article_id
GROUP BY a.id;
*/

-- Query 3: Get image review history for an article
-- Uses idx_article_image_reviews_article_image
/*
SELECT
    air.id,
    ai.position,
    ai.caption,
    air.action,
    air.new_caption,
    air.new_source_url,
    air.reviewer_notes,
    air.created_at
FROM article_image_reviews air
JOIN article_images ai ON air.article_image_id = ai.id
WHERE ai.article_id = :article_id
ORDER BY ai.position, air.created_at DESC;
*/


-- ============================================================================
-- 6. DATA MIGRATION NOTES
-- ============================================================================

-- When running the Alembic migration, consider the following data transformations:

-- 1. Migrate existing 'title' field to 'title_main':
--    UPDATE articles SET title_main = title WHERE title_main IS NULL OR title_main = '';

-- 2. For existing articles without parsing confirmation:
--    UPDATE articles SET parsing_confirmed = TRUE WHERE status IN ('published', 'ready_to_publish');
--    (Assume articles already in late stages were implicitly parsed correctly)

-- 3. Backfill body_html from existing 'body' field if needed:
--    UPDATE articles SET body_html = body WHERE body_html IS NULL;

-- 4. For articles with existing tags:
--    -- tags TEXT[] already exists and is compatible with the new schema


-- ============================================================================
-- 7. ROLLBACK / DOWNGRADE
-- ============================================================================

-- To rollback this schema (use in Alembic downgrade):
/*
DROP TRIGGER IF EXISTS update_article_images_updated_at ON article_images;
DROP TABLE IF EXISTS article_image_reviews CASCADE;
DROP TABLE IF EXISTS article_images CASCADE;

ALTER TABLE articles DROP COLUMN IF EXISTS parsing_feedback;
ALTER TABLE articles DROP COLUMN IF EXISTS parsing_confirmed_by;
ALTER TABLE articles DROP COLUMN IF EXISTS parsing_confirmed_at;
ALTER TABLE articles DROP COLUMN IF EXISTS parsing_confirmed;
ALTER TABLE articles DROP COLUMN IF EXISTS seo_keywords;
ALTER TABLE articles DROP COLUMN IF EXISTS meta_description;
ALTER TABLE articles DROP COLUMN IF EXISTS body_html;
ALTER TABLE articles DROP COLUMN IF EXISTS author_name;
ALTER TABLE articles DROP COLUMN IF EXISTS author_line;
ALTER TABLE articles DROP COLUMN IF EXISTS title_suffix;
ALTER TABLE articles DROP COLUMN IF EXISTS title_main;
ALTER TABLE articles DROP COLUMN IF EXISTS title_prefix;

DROP INDEX IF EXISTS idx_articles_parsing_confirmed_at;
DROP INDEX IF EXISTS idx_articles_parsing_confirmed;
*/


-- ============================================================================
-- END OF SCHEMA DESIGN
-- ============================================================================
