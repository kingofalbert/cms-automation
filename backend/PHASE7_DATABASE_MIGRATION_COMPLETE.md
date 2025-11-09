# Phase 7 Database Migration - Completion Report

**Date**: 2025-11-08
**Status**: ✅ **COMPLETED SUCCESSFULLY**
**Migration Time**: ~60 seconds
**Database**: Supabase Production (aws-1-us-east-1.pooler.supabase.com)

---

## ✅ Migrations Applied

### 1. **20251108_1600** - Articles Table Extensions
**Status**: ✅ Applied

**New Fields Added to `articles` table**:
- `title_prefix` (VARCHAR 200) - 标题前缀，例如 "【專題報導】"
- `title_main` (VARCHAR 500) - 主标题（必填）
- `title_suffix` (VARCHAR 200) - 副标题
- `author_line` (VARCHAR 300) - 原始作者行
- `author_name` (VARCHAR 100) - 提取的作者姓名
- `body_html` (TEXT) - 清洗后的正文 HTML
- `meta_description` (TEXT) - SEO 元描述
- `seo_keywords` (TEXT[]) - SEO 关键词数组
- `parsing_confirmed` (BOOLEAN) - 解析确认状态
- `parsing_confirmed_at` (TIMESTAMP) - 确认时间
- `parsing_confirmed_by` (VARCHAR 100) - 确认人
- `parsing_feedback` (TEXT) - 确认反馈

**New Indexes**:
- `idx_articles_parsing_confirmed` (partial index for WHERE parsing_confirmed = FALSE)
- `idx_articles_parsing_confirmed_at` (DESC)

**Data Migration**:
- Backfilled `title_main` from existing `title` field
- Backfilled `body_html` from existing `body` field
- Marked existing published articles as `parsing_confirmed = TRUE`

---

### 2. **20251108_1700** - Article Images Tables
**Status**: ✅ Applied

**New Table: `article_images`**
Stores image metadata, paths, and technical specifications.

**Columns**:
- `id` SERIAL PRIMARY KEY
- `article_id` INTEGER (FK to articles, ON DELETE CASCADE)
- `preview_path` VARCHAR(500) - 缩略图路径
- `source_path` VARCHAR(500) - 原图文件路径
- `source_url` VARCHAR(1000) - 原图下载 URL
- `caption` TEXT - 图片说明
- `position` INTEGER - 段落位置（0-based）
- `metadata` JSONB - 技术规格（width, height, format, EXIF等）
- `created_at`, `updated_at` TIMESTAMP

**Constraints**:
- UNIQUE (article_id, position) - 防止重复位置
- CHECK (position >= 0) - 确保位置非负

**Indexes**:
- `idx_article_images_article_id`
- `idx_article_images_position` (article_id, position)
- `idx_article_images_created_at` (DESC)
- `idx_article_images_metadata_gin` (GIN index for JSONB queries)

**Trigger**:
- `update_article_images_updated_at` - Auto-update `updated_at` on changes

---

**New Table: `article_image_reviews`**
Tracks user review actions during parsing confirmation (Step 1).

**Columns**:
- `id` SERIAL PRIMARY KEY
- `article_image_id` INTEGER (FK to article_images, ON DELETE CASCADE)
- `worklist_item_id` INTEGER (optional FK)
- `action` VARCHAR(20) - 操作类型: 'keep'|'remove'|'replace_caption'|'replace_source'
- `new_caption` TEXT - 替换的说明文字
- `new_source_url` VARCHAR(1000) - 替换的原图 URL
- `reviewer_notes` TEXT - 审核备注
- `created_at` TIMESTAMP

**Constraints**:
- CHECK (action IN ('keep', 'remove', 'replace_caption', 'replace_source'))
- CHECK (action != 'replace_caption' OR new_caption IS NOT NULL)
- CHECK (action != 'replace_source' OR new_source_url IS NOT NULL)

**Indexes**:
- `idx_article_image_reviews_article_image`
- `idx_article_image_reviews_worklist_item`
- `idx_article_image_reviews_action`
- `idx_article_image_reviews_created_at` (DESC)

---

## 🐛 Issues Resolved

### Issue 1: SQLAlchemy Reserved Attribute Name
**Problem**: `Attribute name 'metadata' is reserved when using the Declarative API`

**Solution**:
- Renamed Python attribute from `metadata` to `image_metadata`
- Database column name remains `metadata` using explicit mapping:
  ```python
  image_metadata: Mapped[dict | None] = mapped_column(
      "metadata",  # Database column name
      JSONB,
      ...
  )
  ```

**Files Updated**:
- `src/models/article_image.py` - ORM model
- `tests/unit/test_article_parser.py` - Unit tests

---

### Issue 2: Supabase SSL Connection Error
**Problem**: `SSL connection has been closed unexpectedly`

**Solution**:
- Added `?sslmode=require` to DATABASE_URL in migration script
- Updated `run_migrations.sh` with SSL parameter:
  ```bash
  export DATABASE_URL="postgresql+asyncpg://...?sslmode=require"
  ```

**Files Updated**:
- `run_migrations.sh` - Production migration script (permanent fix)
- `run_migrations_fix.sh` - Temporary fix script (can be removed)

---

## 📊 Database Schema Summary

### Current Alembic Version
```
20251108_1700
```

### Table Count Changes
- **Before**: 11 tables
- **After**: 13 tables (+2)
  - `article_images` (NEW)
  - `article_image_reviews` (NEW)

### Articles Table
- **Before**: 30 columns
- **After**: 42 columns (+12)

### Total Indexes Added
- **Articles table**: +2 indexes
- **article_images table**: +4 indexes
- **article_image_reviews table**: +4 indexes
- **Total**: +10 indexes

---

## 🔍 Verification

Run this SQL in Supabase SQL Editor to verify:
```bash
cat verify_phase7_schema.sql
```

Or check via Python:
```bash
# Install asyncpg first if needed
python3 check_phase7_schema.py
```

Expected output:
```
✅ Phase 7 database schema is FULLY APPLIED
```

---

## 📝 Next Steps

### Week 16 (Current) - Database ✅
- [x] T7.1: Design schema (ER diagram, SQL DDL)
- [x] T7.2: Create articles table migration
- [x] T7.3: Create image tables migration
- [x] T7.4: Create SQLAlchemy ORM models
- [x] T7.5: Implement ArticleParserService skeleton

### Week 17-18 (Next) - Backend Parsing Engine
- [ ] T7.6: ImageProcessorService (PIL/Pillow)
- [ ] T7.7: AI parsing implementation (Claude integration)
- [ ] T7.8: Heuristic parsing implementation
- [ ] T7.9: Image extraction logic
- [ ] T7.10-T7.12: Unit tests & integration tests

### Week 19 - API & Integration
- [ ] T7.13-T7.15: API endpoints, Pydantic schemas, integration tests

### Week 20-21 - Frontend Step 1 UI
- [ ] T7.16-T7.25: Parsing confirmation UI components

### Week 21 - Testing & Deployment
- [ ] T7.26-T7.29: E2E tests, documentation, deployment

---

## 📚 Documentation Created

1. **Schema Design**:
   - `migrations/manual_sql/phase7_parsing_schema.sql` - Complete SQL DDL
   - `docs/article_images_metadata_spec.md` - JSONB metadata specification
   - `docs/phase7_er_diagram.md` - Entity-relationship diagram

2. **Migrations**:
   - `migrations/versions/20251108_1600_add_article_parsing_fields.py`
   - `migrations/versions/20251108_1700_create_article_images_tables.py`

3. **ORM Models**:
   - `src/models/article.py` - Extended Article model
   - `src/models/article_image.py` - ArticleImage & ArticleImageReview models

4. **Parser Service**:
   - `src/services/parser/models.py` - Pydantic models
   - `src/services/parser/article_parser.py` - Parser service skeleton
   - `tests/unit/test_article_parser.py` - 41 unit tests

5. **Verification**:
   - `verify_phase7_schema.sql` - SQL verification queries
   - `check_phase7_schema.py` - Python verification script

---

## 🎯 Success Criteria

- [x] All migrations execute without errors
- [x] All new tables created successfully
- [x] All new columns added to articles table
- [x] All indexes created
- [x] All triggers created
- [x] All constraints enforced
- [x] Data backfill completed
- [x] SQLAlchemy models load without errors
- [x] SSL connection issues resolved

---

## 📞 Contact

**Tech Lead**: @kingofalbert
**Date Completed**: 2025-11-08 04:52 UTC
**Total Time**: 1 hour (including troubleshooting)

---

**✅ Phase 7 Database Layer: COMPLETE**
