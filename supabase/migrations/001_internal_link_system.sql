-- ============================================================
-- Internal Link System - Database Setup (V2)
-- Version: 2.0
-- Date: 2025-12-07
-- Updated: Added full article parsing fields
-- ============================================================

-- ============================================================
-- STEP 1: Enable Required Extensions
-- ============================================================

-- Enable pgvector for vector similarity search
-- Note: On Supabase, vector extension may be in 'public' schema instead of 'extensions'
create extension if not exists vector;

-- Enable pg_cron for scheduled tasks (requires Supabase Pro plan or self-hosted)
-- Note: If using Supabase Free tier, skip this and use external cron
create extension if not exists pg_cron with schema extensions;

-- Enable pg_net for HTTP calls from PostgreSQL
create extension if not exists pg_net with schema extensions;

-- ============================================================
-- STEP 2: Create Health Articles Table (Enhanced)
-- ============================================================

create table if not exists public.health_articles (
    id bigint primary key generated always as identity,

    -- ===== 原始爬取數據 (DOM 解析，無 AI) =====
    original_url text not null unique,
    article_id text not null unique,  -- 從 URL 提取 (e.g., n12345678)

    -- 標題 (完整標題 + AI 分解)
    title text not null,                    -- 完整原始標題
    title_prefix text,                      -- AI 分解：前綴 (如【專題】)
    title_main text,                        -- AI 分解：主標題
    title_suffix text,                      -- AI 分解：副標題

    -- 作者信息
    author_line text,                       -- 原始作者行 (如 "文／張三｜編輯／李四")
    author_name text,                       -- AI 清理後的作者名

    -- 內容字段
    body_html text,                         -- 正文 HTML (清理後)
    excerpt text,                           -- 文章摘要/導語
    word_count int,                         -- 正文字數統計

    -- 分類和標籤
    category text default '健康',           -- 原始爬取的欄目分類
    original_tags text[] default '{}',      -- 原始爬取的標籤
    primary_category text,                  -- AI 驗證後的主分類
    secondary_categories text[] default '{}', -- AI 推斷的副分類

    -- 日期
    publish_date date,                      -- 發佈日期

    -- ===== AI 增強數據 (GPT-4o-mini) =====
    ai_keywords text[] default '{}',        -- AI 提取的關鍵詞 (3-5 個)
    seo_title text,                         -- AI 生成的 SEO 標題 (可選)
    seo_title_source text default 'none'    -- SEO 標題來源: none/ai_generated
        check (seo_title_source in ('none', 'ai_generated', 'extracted')),

    -- ===== 向量嵌入數據 =====
    title_embedding vector(1536),    -- 標題向量
    content_embedding vector(1536),  -- 正文向量 (可選，用於深度匹配)

    -- ===== 處理狀態追蹤 =====
    status text default 'scraped' check (status in (
        'scraped',          -- 階段1完成：已爬取 DOM (正文、圖片)
        'parsed',           -- 階段2完成：AI 增強解析 (標題分解、關鍵詞)
        'embedded',         -- 階段3完成：向量嵌入生成
        'ready'             -- 全部完成，可用於匹配
    )),

    -- ===== AI 功能標記 =====
    -- 明確標記哪些 AI 功能可用/不可用
    ai_features jsonb default '{
        "keywords": "available",
        "title_decomposition": "available",
        "category_inference": "available",
        "faq_generation": "not_available",
        "deep_seo": "not_available",
        "proofreading": "not_available"
    }'::jsonb,

    -- ===== 時間戳 =====
    scraped_at timestamptz default now(),   -- 爬取時間
    parsed_at timestamptz,                  -- AI 解析時間
    embedded_at timestamptz,                -- 向量生成時間
    updated_at timestamptz default now()
);

-- Add comments for documentation
comment on table public.health_articles is '大紀元健康文章存儲表 - 用於內部鏈接推薦';
comment on column public.health_articles.article_id is '文章唯一標識符，從 URL 提取 (如 n12345678)';
comment on column public.health_articles.title is '完整原始標題';
comment on column public.health_articles.title_prefix is 'AI 分解的標題前綴 (如【專題】)';
comment on column public.health_articles.title_main is 'AI 分解的主標題';
comment on column public.health_articles.title_suffix is 'AI 分解的副標題';
comment on column public.health_articles.body_html is '清理後的正文 HTML';
comment on column public.health_articles.ai_keywords is 'GPT-4o-mini 提取的關鍵詞 (3-5 個)';
comment on column public.health_articles.ai_features is 'AI 功能可用性標記，避免誤導';
comment on column public.health_articles.status is '處理狀態: scraped -> parsed -> embedded -> ready';

-- ============================================================
-- STEP 3: Create Health Article Images Table
-- ============================================================

create table if not exists public.health_article_images (
    id bigint primary key generated always as identity,
    article_id text not null,
    position int not null default 0,        -- 圖片在文章中的位置 (0-based)
    source_url text not null,               -- 原始圖片 URL
    caption text,                           -- 圖片標題/說明
    alt_text text,                          -- 替代文字 (無障礙)
    width int,                              -- 圖片寬度 (如果可獲取)
    height int,                             -- 圖片高度 (如果可獲取)
    is_featured boolean default false,      -- 是否為特色圖片
    created_at timestamptz default now(),

    -- Foreign key constraint
    constraint fk_article
        foreign key (article_id)
        references public.health_articles(article_id)
        on delete cascade
);

comment on table public.health_article_images is '健康文章圖片元數據';

-- Index for querying images by article
create index if not exists idx_health_article_images_article
on public.health_article_images(article_id);

-- ============================================================
-- STEP 4: Create Indexes for Performance
-- ============================================================

-- Status index for filtering by processing status
create index if not exists idx_health_articles_status
on public.health_articles(status);

-- Article ID index for quick lookups
create index if not exists idx_health_articles_article_id
on public.health_articles(article_id);

-- Publish date index for chronological queries
create index if not exists idx_health_articles_publish_date
on public.health_articles(publish_date desc);

-- GIN index for keyword array searching
create index if not exists idx_health_articles_keywords
on public.health_articles using gin(ai_keywords);

-- GIN index for original tags searching
create index if not exists idx_health_articles_original_tags
on public.health_articles using gin(original_tags);

-- Category index
create index if not exists idx_health_articles_category
on public.health_articles(category);

-- HNSW vector index for title embedding (efficient ANN search)
create index if not exists idx_health_articles_title_embedding
on public.health_articles using hnsw (title_embedding vector_cosine_ops)
with (m = 16, ef_construction = 64);

-- HNSW vector index for content embedding (optional, for deep matching)
create index if not exists idx_health_articles_content_embedding
on public.health_articles using hnsw (content_embedding vector_cosine_ops)
with (m = 16, ef_construction = 64);

-- ============================================================
-- STEP 5: Create Scrape Jobs Table
-- ============================================================

create table if not exists public.scrape_jobs (
    id bigint primary key generated always as identity,
    job_type text not null check (job_type in ('scrape', 'parse', 'embedding')),
    started_at timestamptz default now(),
    completed_at timestamptz,
    articles_processed int default 0,
    articles_new int default 0,
    articles_failed int default 0,
    status text default 'running' check (status in ('running', 'completed', 'failed')),
    error_message text,
    metadata jsonb default '{}'
);

comment on table public.scrape_jobs is '爬取和處理任務執行歷史';

-- Index for querying recent jobs
create index if not exists idx_scrape_jobs_type_date
on public.scrape_jobs(job_type, started_at desc);

-- ============================================================
-- STEP 6: Create Internal Link Suggestions Cache Table
-- ============================================================

create table if not exists public.internal_link_suggestions (
    id bigint primary key generated always as identity,
    source_article_id text not null,
    target_article_id text not null,
    similarity_score float not null,
    match_type text not null check (match_type in ('semantic', 'keyword', 'tag')),
    created_at timestamptz default now(),

    -- Foreign key constraints
    constraint fk_source_article
        foreign key (source_article_id)
        references public.health_articles(article_id)
        on delete cascade,
    constraint fk_target_article
        foreign key (target_article_id)
        references public.health_articles(article_id)
        on delete cascade,

    -- Unique constraint to prevent duplicate suggestions
    unique(source_article_id, target_article_id)
);

comment on table public.internal_link_suggestions is '內部鏈接推薦緩存';

-- Index for querying suggestions by source article
create index if not exists idx_link_suggestions_source
on public.internal_link_suggestions(source_article_id);

-- ============================================================
-- STEP 7: Create Vector Similarity Search Function
-- ============================================================

create or replace function public.match_health_articles(
    query_embedding vector(1536),
    match_threshold float default 0.7,
    match_count int default 5,
    exclude_article_id text default null
)
returns table (
    id bigint,
    article_id text,
    title text,
    title_main text,
    original_url text,
    ai_keywords text[],
    excerpt text,
    similarity float
)
language plpgsql
security definer
set search_path = public
as $$
begin
    return query
    select
        ha.id,
        ha.article_id,
        ha.title,
        ha.title_main,
        ha.original_url,
        ha.ai_keywords,
        ha.excerpt,
        1 - (ha.title_embedding <=> query_embedding) as similarity
    from public.health_articles ha
    where
        ha.status = 'ready'
        and ha.title_embedding is not null
        and (exclude_article_id is null or ha.article_id != exclude_article_id)
        and 1 - (ha.title_embedding <=> query_embedding) > match_threshold
    order by ha.title_embedding <=> query_embedding
    limit match_count;
end;
$$;

comment on function public.match_health_articles is '使用向量余弦相似度搜索相關文章';

-- ============================================================
-- STEP 8: Create Keyword Matching Function
-- ============================================================

create or replace function public.match_by_keywords(
    source_keywords text[],
    match_count int default 5,
    exclude_article_id text default null
)
returns table (
    article_id text,
    title text,
    title_main text,
    original_url text,
    matched_keywords text[],
    match_score int
)
language plpgsql
security definer
set search_path = public
as $$
begin
    return query
    select
        ha.article_id,
        ha.title,
        ha.title_main,
        ha.original_url,
        array(
            select unnest(ha.ai_keywords)
            intersect
            select unnest(source_keywords)
        ) as matched_keywords,
        cardinality(
            array(
                select unnest(ha.ai_keywords)
                intersect
                select unnest(source_keywords)
            )
        ) as match_score
    from public.health_articles ha
    where
        ha.status = 'ready'
        and (exclude_article_id is null or ha.article_id != exclude_article_id)
        and ha.ai_keywords && source_keywords  -- Array overlap operator
    order by match_score desc
    limit match_count;
end;
$$;

comment on function public.match_by_keywords is '使用關鍵詞數組交集匹配文章';

-- ============================================================
-- STEP 9: Create Content-based Similarity Search Function
-- ============================================================

create or replace function public.match_by_content(
    query_embedding vector(1536),
    match_threshold float default 0.6,
    match_count int default 5,
    exclude_article_id text default null
)
returns table (
    id bigint,
    article_id text,
    title text,
    original_url text,
    excerpt text,
    similarity float
)
language plpgsql
security definer
set search_path = public
as $$
begin
    return query
    select
        ha.id,
        ha.article_id,
        ha.title,
        ha.original_url,
        ha.excerpt,
        1 - (ha.content_embedding <=> query_embedding) as similarity
    from public.health_articles ha
    where
        ha.status = 'ready'
        and ha.content_embedding is not null
        and (exclude_article_id is null or ha.article_id != exclude_article_id)
        and 1 - (ha.content_embedding <=> query_embedding) > match_threshold
    order by ha.content_embedding <=> query_embedding
    limit match_count;
end;
$$;

comment on function public.match_by_content is '使用正文向量進行深度內容匹配';

-- ============================================================
-- STEP 10: Create Updated_at Trigger
-- ============================================================

create or replace function public.update_updated_at_column()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

-- Apply trigger to health_articles
drop trigger if exists update_health_articles_updated_at on public.health_articles;
create trigger update_health_articles_updated_at
    before update on public.health_articles
    for each row
    execute function public.update_updated_at_column();

-- ============================================================
-- STEP 11: Row Level Security (RLS)
-- ============================================================

-- Enable RLS
alter table public.health_articles enable row level security;
alter table public.health_article_images enable row level security;
alter table public.scrape_jobs enable row level security;
alter table public.internal_link_suggestions enable row level security;

-- Create policies for service role access (Edge Functions)
create policy "Service role full access to health_articles"
on public.health_articles
for all
to service_role
using (true)
with check (true);

create policy "Service role full access to health_article_images"
on public.health_article_images
for all
to service_role
using (true)
with check (true);

create policy "Service role full access to scrape_jobs"
on public.scrape_jobs
for all
to service_role
using (true)
with check (true);

create policy "Service role full access to internal_link_suggestions"
on public.internal_link_suggestions
for all
to service_role
using (true)
with check (true);

-- Create policies for anon access (read-only for API queries)
create policy "Anon read access to health_articles"
on public.health_articles
for select
to anon
using (status = 'ready');

create policy "Anon read access to health_article_images"
on public.health_article_images
for select
to anon
using (true);

create policy "Anon read access to internal_link_suggestions"
on public.internal_link_suggestions
for select
to anon
using (true);

-- ============================================================
-- STEP 12: Helper Views
-- ============================================================

-- View for monitoring processing status
create or replace view public.v_processing_status as
select
    status,
    count(*) as article_count,
    round(100.0 * count(*) / nullif(sum(count(*)) over (), 0), 2) as percentage
from public.health_articles
group by status
order by
    case status
        when 'scraped' then 1
        when 'parsed' then 2
        when 'embedded' then 3
        when 'ready' then 4
    end;

comment on view public.v_processing_status is '文章處理狀態分布統計';

-- View for recent job history
create or replace view public.v_recent_jobs as
select
    id,
    job_type,
    started_at,
    completed_at,
    articles_processed,
    articles_new,
    articles_failed,
    status,
    error_message,
    extract(epoch from (completed_at - started_at))::int as duration_seconds
from public.scrape_jobs
order by started_at desc
limit 50;

comment on view public.v_recent_jobs is '最近的任務執行歷史';

-- View for articles with images count
create or replace view public.v_articles_with_images as
select
    ha.article_id,
    ha.title,
    ha.title_main,
    ha.status,
    ha.category,
    ha.publish_date,
    count(hai.id) as image_count,
    ha.word_count
from public.health_articles ha
left join public.health_article_images hai on ha.article_id = hai.article_id
group by ha.article_id, ha.title, ha.title_main, ha.status, ha.category, ha.publish_date, ha.word_count
order by ha.scraped_at desc;

comment on view public.v_articles_with_images is '文章及其圖片數量概覽';

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Check extensions are enabled
-- select * from pg_extension where extname in ('vector', 'pg_cron', 'pg_net');

-- Check tables were created
-- select table_name from information_schema.tables where table_schema = 'public';

-- Check functions were created
-- select routine_name from information_schema.routines where routine_schema = 'public';

-- Check indexes were created
-- select indexname from pg_indexes where schemaname = 'public';
