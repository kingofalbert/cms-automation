-- Migration: Add featured image detection fields
-- Date: 2025-12-20
-- Description: Add is_featured, image_type, detection_method fields to article_images
-- for proper separation of featured (置頂) images and content images

-- ============================================================
-- Step 1: Add new columns
-- ============================================================

-- is_featured: Boolean flag for featured image
ALTER TABLE article_images
ADD COLUMN IF NOT EXISTS is_featured BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN article_images.is_featured IS 'Whether this is the featured/cover image (置頂圖片)';

-- image_type: Categorize image type
ALTER TABLE article_images
ADD COLUMN IF NOT EXISTS image_type VARCHAR(20) NOT NULL DEFAULT 'content';

COMMENT ON COLUMN article_images.image_type IS 'Image type: featured (置頂) / content (正文) / inline (行內)';

-- detection_method: How featured status was determined
ALTER TABLE article_images
ADD COLUMN IF NOT EXISTS detection_method VARCHAR(50);

COMMENT ON COLUMN article_images.detection_method IS 'How featured status was detected: caption_keyword / position_before_body / manual';

-- ============================================================
-- Step 2: Add check constraint for image_type
-- ============================================================

ALTER TABLE article_images
ADD CONSTRAINT article_images_valid_image_type
CHECK (image_type IN ('featured', 'content', 'inline'));

-- ============================================================
-- Step 3: Migrate existing data
-- Position = 0 images are treated as featured (legacy behavior)
-- ============================================================

UPDATE article_images
SET
    is_featured = TRUE,
    image_type = 'featured',
    detection_method = 'position_legacy'
WHERE position = 0
  AND is_featured = FALSE;

-- ============================================================
-- Step 4: Create indexes for efficient querying
-- ============================================================

-- Index for finding featured image per article
CREATE INDEX IF NOT EXISTS idx_article_images_featured
ON article_images(article_id, is_featured)
WHERE is_featured = TRUE;

-- Index for filtering by image type
CREATE INDEX IF NOT EXISTS idx_article_images_type
ON article_images(article_id, image_type);

-- ============================================================
-- Step 5: Create helper function (optional)
-- ============================================================

-- Function to get featured image for an article
CREATE OR REPLACE FUNCTION get_featured_image(p_article_id INTEGER)
RETURNS TABLE (
    id INTEGER,
    source_url VARCHAR(1000),
    caption TEXT,
    preview_path VARCHAR(500),
    detection_method VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ai.id,
        ai.source_url,
        ai.caption,
        ai.preview_path,
        ai.detection_method
    FROM article_images ai
    WHERE ai.article_id = p_article_id
      AND ai.is_featured = TRUE
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Verification queries (run manually to verify migration)
-- ============================================================

-- Check column existence:
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'article_images'
-- AND column_name IN ('is_featured', 'image_type', 'detection_method');

-- Check migrated data:
-- SELECT image_type, is_featured, detection_method, COUNT(*)
-- FROM article_images
-- GROUP BY image_type, is_featured, detection_method;

-- Check featured images per article:
-- SELECT article_id, COUNT(*) as featured_count
-- FROM article_images
-- WHERE is_featured = TRUE
-- GROUP BY article_id
-- HAVING COUNT(*) > 1;
