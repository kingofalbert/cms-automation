# Article Parsing & Structured Storage Requirements

## Context

Current Google Doc ingestion (handled inside `backend/src/services/google_drive`) stores the entire document as a single HTML blob with minimal metadata. The Proofreading Review page therefore mixes parsing validation, SEO review, and language QA on one screen. We now introduce a normalized parsing layer so Step 1 of Proofreading can focus on “解析確認”.

## Functional Goals

1. **Structured Headers**  
   - Treat line breaks (line = text between carriage returns) as the delimiter for the header block.  
   - Mapping rules:  
     * **Three lines** → line 1 → `title_prefix`, line 2 → `title_main`, line 3 → `title_suffix`.  
     * **Two lines** → line 1 → `title_main`, line 2 → `title_suffix`.  
     * **One line** → that line is `title_main`.  
   - If the imported doc uses visual separators (`｜`, `—`, `：`) within the same line, fallback heuristics split them into prefix/main/suffix.  
   - Persist to `articles` table and expose via `/v1/worklist/:id`.

2. **Author Line Extraction**  
   - Identify the first line under the title that matches `文／XXX` or similar (`撰稿`, `作者`).  
   - Persist both raw line (`author_line`) and cleaned name (`author_name`).

3. **Body HTML Cleanup**  
   - Remove the extracted header, author, image blocks, and meta/SEO sections from the DOM.  
   - Preserve the remaining DOM structure (H1/H2, bold, lists) and store as `body_html`.  
   - Ensure sanitized HTML (reuse existing sanitizer) while keeping semantic tags.

4. **Image Groups**  
   - For each inline image block: capture preview image, caption, and the “原圖/點此下載” source link.  
   - Download the high-resolution source image (using `source_url`) into the chosen media backend (decision pending: Google Drive vs Supabase storage).  
   - Create `article_images` records with fields:  
     `article_id`, `preview_path`, `source_path`, `source_url`, `caption`, `position`, `metadata`.  
   - `position` = zero-based index of the paragraph before which the image appeared (requires paragraph-level tokenization during parsing).
   - While downloading, record image specifications (width, height, aspect ratio, file size, mime type, EXIF date) inside `metadata`.  
   - Step 1 UI must surface these specs so reviewers can confirm the correct source asset was captured (future design doc will enumerate the exact metrics list).

5. **Meta / SEO Fields**  
   - Detect terminal blocks labelled `Meta Description：`, `關鍵詞：`, `Tags：` (support English labels).  
   - Strip them from DOM after extraction.  
   - Persist:  
     * `meta_description` (string)  
     * `seo_keywords` (array of strings)  
     * `tags` (array of strings mapped to CMS taxonomy)

6. **API Exposure & Review UX**  
   - Extend `/v1/worklist/:id` and related DTOs to return the structured fields and image list.  
   - Proofreading Review Step 1 uses these fields to let reviewers confirm parsing before proceeding with SEO/校對 decisions.

## Frontend Responsibilities

1. **Proofreading Review Step 1 UI**  
   - Introduce a stepper/wizard (or collapsible sections) showing:  
     * Structured headers + author line  
     * Image gallery (preview + caption + source link)  
     * Parsed meta description / keywords / tags  
     * Cleaned body HTML preview  
   - Provide inline “Looks good / needs fix” toggles (persisted via existing review payload with new `step` metadata).  
   - Step 1 must block access to Step 2 (正文校對) until the parsing confirmation is recorded; reviewers can return to Step 1 to adjust their feedback.

2. **Worklist Item Drawer / Detail Panels**  
   - Display parsed images and metadata (read-only) to give operations visibility before entering review mode.
   - The image table should show the recorded specifications (resolution, file size, mime) and highlight any assets that fall outside publishing tolerances (thresholds to be defined in upcoming image-spec doc).

3. **Localization**  
   - All new labels must use `t('proofreading.parsing.*')` namespace (update `en-US` / `zh-TW` locale files).

## Backend Responsibilities

1. **Parser Pipeline**  
   - Implement an AI-driven parser module (e.g., `backend/src/services/parser/article_parser.py`) invoked during Google Doc import / drive sync.  
   - Use the same large language model configuration as the Proofreading pipeline (current default: Claude 4.5 Sonnet) to interpret the document structure; fallback heuristics/scripts only handle sanitization and DOM cleanup.  
   - Steps:  
     1. Convert Google Doc to HTML/Markdown (existing step).  
     2. Parse headings/author per heuristics (regex + DOM traversal).  
     3. Iterate DOM nodes, collect image groups, download originals, replace inline nodes with placeholders or remove.  
     4. Detect meta blocks; capture + remove.  
     5. Serialize remaining DOM as sanitized HTML.

2. **Persistence**  
   - Alter `articles` table (and mirrored worklist table) to add:  
     `title_prefix`, `title_main`, `title_suffix`, `author_line`, `author_name`, `meta_description`, `seo_keywords` (array), `tags` (array), `body_html`.  
   - Create `article_images` table as defined above, plus indexes on `article_id` and `position`.  
   - Store binary assets in the agreed storage and persist normalized paths.
   - Extend review-state tables to capture parser confirmation: e.g. add `parsing_confirmed_at`, `parsing_confirmed_by`, and `parsing_feedback` columns on `worklist_items` / `proofreading_reviews`, so Step 1 decisions are traceable.
   - For image edits during proofreading (e.g., replacing captions or removing a picture), persist reviewer decisions in `article_image_reviews` (child table) linking to `article_images`.

3. **API & DTO Updates**  
   - `/v1/worklist`, `/v1/worklist/:id`, `/v1/articles/:id` should return the structured fields and image list.  
   - Update serializers and Pydantic models in `backend/src/api/routes` & `backend/src/services/proofreading/models.py`.

4. **Review Payload Changes**  
   - Extend `saveReviewDecisions` payload to accept `step_id` metadata so the backend knows which step reviewer confirmed.  
   - For Step 1, store `parsing_confirmed=true`, confirmation timestamp, reviewer id, and optional notes; optionally allow per-field override (e.g., corrected author name).  
   - Step 2+ (正文校對) continues to store issue-level decisions, but must reference the structured fields (e.g., diffing `body_html`); any adjustments should update the same normalized schema (e.g., editing tags updates `articles.tags` and audit trail).

## Open Decisions / Risks

- **Storage Target**: need final call (Google Drive vs Supabase storage) for downloaded high-res images.  
- **Paragraph Position Tracking**: requires consistent DOM segmentation; may need to assign IDs to each `<p>` before removal.  
- **Legacy Articles**: require backfill script to parse existing records or mark them as “legacy-unparsed”.
- **Image Processing Pipeline (Future)**: before publishing, images must be normalized (resize, format conversion, compression) and uploaded to WordPress via Computer Use / provider workflows; automation should insert the processed images into the correct block positions. Detailed specs (allowed formats, max size, responsive crops) will be supplied separately.

## Next Steps

1. Confirm storage backend and update infrastructure secrets accordingly.  
2. Align DB migration plan (articles + article_images).  
3. Implement parser + unit tests (mock Google Doc HTML).  
4. Build Proofreading Step 1 UI with feature flag, gradually roll out.
