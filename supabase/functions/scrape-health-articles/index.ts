/**
 * Scrape Health Articles Edge Function (V2)
 *
 * 完整爬取大紀元健康文章：
 * 1. 從列表頁獲取文章 URL
 * 2. 訪問每篇文章詳情頁
 * 3. DOM 解析提取完整內容（標題、作者、正文、圖片）
 *
 * @version 2.0
 * @date 2025-12-07
 */

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { DOMParser, Element } from 'https://deno.land/x/deno_dom@v0.1.38/deno-dom-wasm.ts'

// ============================================================
// Configuration
// ============================================================

const HEALTH_CATEGORIES = [
  { url: '/b5/nf2283.htm', name: '健康養生' },
  { url: '/b5/ncid248.htm', name: '食療養生' },
  { url: '/b5/ncid246.htm', name: '健康生活' },
]

const BASE_URL = 'https://www.epochtimes.com'
const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
const LIST_PAGE_DELAY_MS = 500      // 列表頁間延遲
const DETAIL_PAGE_DELAY_MS = 1000   // 詳情頁間延遲（更禮貌）
const MAX_PAGES_PER_CATEGORY = 100
const MAX_CONSECUTIVE_EXISTING = 10

// ============================================================
// Types
// ============================================================

interface ArticleBasicInfo {
  url: string
  articleId: string
}

interface ArticleFullInfo {
  // 基本信息
  url: string
  articleId: string

  // 標題
  title: string

  // 作者
  authorLine: string | null

  // 內容
  bodyHtml: string
  excerpt: string | null
  wordCount: number

  // 分類和標籤
  category: string
  tags: string[]

  // 日期
  publishDate: string | null

  // 圖片
  images: ImageInfo[]
}

interface ImageInfo {
  position: number
  sourceUrl: string
  caption: string | null
  altText: string | null
  isFeatured: boolean
}

interface ScrapeResult {
  success: boolean
  processed: number
  new: number
  failed: number
  errors: string[]
}

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
}

// ============================================================
// Main Handler
// ============================================================

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

    if (!supabaseUrl || !supabaseKey) {
      throw new Error('Missing Supabase configuration')
    }

    const supabase = createClient(supabaseUrl, supabaseKey)

    // Parse request options
    const body = await req.json().catch(() => ({}))
    const maxPagesPerCategory = body.maxPages || MAX_PAGES_PER_CATEGORY
    const incrementalOnly = body.incrementalOnly ?? true
    const maxArticlesPerRun = body.maxArticles || 50 // 每次運行最多處理的文章數

    // Create job record
    const { data: job } = await supabase
      .from('scrape_jobs')
      .insert({
        job_type: 'scrape',
        metadata: { incrementalOnly, maxPagesPerCategory, maxArticlesPerRun }
      })
      .select()
      .single()

    const result: ScrapeResult = {
      success: true,
      processed: 0,
      new: 0,
      failed: 0,
      errors: []
    }

    let totalNewArticles = 0

    // Phase 1: Get article URLs from list pages
    console.log('Phase 1: Collecting article URLs from list pages...')

    for (const category of HEALTH_CATEGORIES) {
      if (totalNewArticles >= maxArticlesPerRun) {
        console.log(`Reached max articles limit (${maxArticlesPerRun}), stopping`)
        break
      }

      console.log(`Scraping category: ${category.name}`)

      const articleUrls = await scrapeListPages(
        category.url,
        maxPagesPerCategory,
        incrementalOnly ? supabase : null
      )

      console.log(`Found ${articleUrls.length} article URLs in ${category.name}`)

      // Phase 2: Scrape each article detail page
      for (const basicInfo of articleUrls) {
        if (totalNewArticles >= maxArticlesPerRun) break

        result.processed++

        try {
          // Check if already exists
          const { data: existing } = await supabase
            .from('health_articles')
            .select('id')
            .eq('article_id', basicInfo.articleId)
            .single()

          if (existing) {
            console.log(`Article ${basicInfo.articleId} already exists, skipping`)
            continue
          }

          // Scrape article detail page
          console.log(`Scraping article: ${basicInfo.articleId}`)
          const articleInfo = await scrapeArticleDetail(basicInfo.url, category.name)

          if (!articleInfo) {
            console.error(`Failed to parse article ${basicInfo.articleId}`)
            result.failed++
            result.errors.push(`Parse failed: ${basicInfo.articleId}`)
            continue
          }

          // Insert article
          const { error: insertError } = await supabase
            .from('health_articles')
            .insert({
              original_url: articleInfo.url,
              article_id: articleInfo.articleId,
              title: articleInfo.title,
              author_line: articleInfo.authorLine,
              body_html: articleInfo.bodyHtml,
              excerpt: articleInfo.excerpt,
              word_count: articleInfo.wordCount,
              category: articleInfo.category,
              original_tags: articleInfo.tags,
              publish_date: articleInfo.publishDate,
              status: 'scraped'
            })

          if (insertError) {
            console.error(`Failed to insert article ${basicInfo.articleId}:`, insertError)
            result.failed++
            result.errors.push(`Insert failed: ${basicInfo.articleId}`)
            continue
          }

          // Insert images
          if (articleInfo.images.length > 0) {
            const imageRecords = articleInfo.images.map(img => ({
              article_id: articleInfo.articleId,
              position: img.position,
              source_url: img.sourceUrl,
              caption: img.caption,
              alt_text: img.altText,
              is_featured: img.isFeatured
            }))

            const { error: imgError } = await supabase
              .from('health_article_images')
              .insert(imageRecords)

            if (imgError) {
              console.warn(`Failed to insert images for ${basicInfo.articleId}:`, imgError)
            }
          }

          result.new++
          totalNewArticles++
          console.log(`✓ Saved article: ${articleInfo.title.substring(0, 50)}...`)

          // Polite delay between detail pages
          await sleep(DETAIL_PAGE_DELAY_MS)

        } catch (err) {
          console.error(`Error processing article ${basicInfo.articleId}:`, err)
          result.failed++
          result.errors.push(`Error: ${basicInfo.articleId} - ${err.message}`)
        }
      }
    }

    // Update job record
    if (job) {
      await supabase
        .from('scrape_jobs')
        .update({
          completed_at: new Date().toISOString(),
          articles_processed: result.processed,
          articles_new: result.new,
          articles_failed: result.failed,
          status: 'completed',
          error_message: result.errors.length > 0 ? result.errors.slice(0, 5).join('; ') : null
        })
        .eq('id', job.id)
    }

    return new Response(
      JSON.stringify({
        success: true,
        processed: result.processed,
        new: result.new,
        failed: result.failed,
        errors: result.errors.slice(0, 10),
        jobId: job?.id
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Scraping error:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

// ============================================================
// Phase 1: Scrape List Pages
// ============================================================

async function scrapeListPages(
  categoryPath: string,
  maxPages: number,
  supabase: any | null
): Promise<ArticleBasicInfo[]> {
  const articles: ArticleBasicInfo[] = []
  let page = 1
  let consecutiveExisting = 0

  while (page <= maxPages) {
    const url = page === 1
      ? `${BASE_URL}${categoryPath}`
      : `${BASE_URL}${categoryPath.replace('.htm', '')}_${page}.htm`

    try {
      const response = await fetch(url, {
        headers: { 'User-Agent': USER_AGENT }
      })

      if (!response.ok) {
        console.log(`List page ${page} returned ${response.status}, stopping`)
        break
      }

      const html = await response.text()
      const doc = new DOMParser().parseFromString(html, 'text/html')
      if (!doc) break

      const links = doc.querySelectorAll('a[href*="/b5/"][href$=".htm"]')
      if (links.length === 0) {
        console.log('No article links found, stopping')
        break
      }

      let pageNewCount = 0

      for (const link of links) {
        const href = (link as Element).getAttribute('href') || ''
        const fullUrl = href.startsWith('http') ? href : `${BASE_URL}${href}`

        // Extract article ID (e.g., n12345678)
        const match = fullUrl.match(/\/(n\d+)\.htm/)
        if (!match) continue

        const articleId = match[1]

        // Check if already exists (for incremental mode)
        if (supabase) {
          const { data: existing } = await supabase
            .from('health_articles')
            .select('id')
            .eq('article_id', articleId)
            .single()

          if (existing) {
            consecutiveExisting++
            if (consecutiveExisting >= MAX_CONSECUTIVE_EXISTING) {
              console.log(`Found ${MAX_CONSECUTIVE_EXISTING} consecutive existing, stopping`)
              return articles
            }
            continue
          }
          consecutiveExisting = 0
        }

        // Avoid duplicates in current batch
        if (!articles.some(a => a.articleId === articleId)) {
          articles.push({ url: fullUrl, articleId })
          pageNewCount++
        }
      }

      console.log(`List page ${page}: found ${pageNewCount} new URLs`)
      page++
      await sleep(LIST_PAGE_DELAY_MS)

    } catch (err) {
      console.error(`Error fetching list page ${page}:`, err)
      break
    }
  }

  return articles
}

// ============================================================
// Phase 2: Scrape Article Detail Page
// ============================================================

async function scrapeArticleDetail(
  url: string,
  category: string
): Promise<ArticleFullInfo | null> {
  try {
    const response = await fetch(url, {
      headers: { 'User-Agent': USER_AGENT }
    })

    if (!response.ok) {
      console.error(`Article page returned ${response.status}: ${url}`)
      return null
    }

    const html = await response.text()
    const doc = new DOMParser().parseFromString(html, 'text/html')
    if (!doc) return null

    // Extract article ID from URL
    const match = url.match(/\/(n\d+)\.htm/)
    if (!match) return null
    const articleId = match[1]

    // ===== Extract Title =====
    const titleEl = doc.querySelector('h1.title, h1, .post_title, article h1')
    const title = titleEl?.textContent?.trim() || ''
    if (!title) {
      console.error('No title found')
      return null
    }

    // ===== Extract Author =====
    const authorEl = doc.querySelector('.author, .post_author, .writer, [class*="author"]')
    const authorLine = authorEl?.textContent?.trim() || null

    // ===== Extract Publish Date =====
    const dateEl = doc.querySelector('time, .date, .post_date, [class*="time"]')
    const dateText = dateEl?.textContent?.trim() || dateEl?.getAttribute('datetime') || ''
    const publishDate = parseDate(dateText)

    // ===== Extract Tags =====
    const tagEls = doc.querySelectorAll('.tags a, .post_tag a, [class*="tag"] a')
    const tags: string[] = []
    for (const tagEl of tagEls) {
      const tag = (tagEl as Element).textContent?.trim()
      if (tag && !tags.includes(tag)) {
        tags.push(tag)
      }
    }

    // ===== Extract Body HTML =====
    const contentEl = doc.querySelector(
      '.post_content, .article_content, article .content, .entry-content, [class*="article-body"]'
    )

    let bodyHtml = ''
    let excerpt: string | null = null
    const images: ImageInfo[] = []

    if (contentEl) {
      // Clone to avoid modifying original
      const contentClone = contentEl.cloneNode(true) as Element

      // Remove unwanted elements
      const removeSelectors = [
        'script', 'style', 'iframe', 'noscript',
        '.ad', '.advertisement', '.social-share',
        '.related-posts', '.comments', 'nav'
      ]
      for (const selector of removeSelectors) {
        const elements = contentClone.querySelectorAll(selector)
        for (const el of elements) {
          (el as Element).remove()
        }
      }

      // Extract images before cleaning
      const imgEls = contentClone.querySelectorAll('img')
      let imgPosition = 0
      for (const imgEl of imgEls) {
        const img = imgEl as Element
        const src = img.getAttribute('src') || img.getAttribute('data-src') || ''

        if (src && !src.startsWith('data:')) {
          const fullSrc = src.startsWith('http') ? src : `${BASE_URL}${src}`

          // Try to find caption
          const figcaption = img.closest('figure')?.querySelector('figcaption')
          const caption = figcaption?.textContent?.trim() || null

          images.push({
            position: imgPosition,
            sourceUrl: fullSrc,
            caption: caption,
            altText: img.getAttribute('alt') || null,
            isFeatured: imgPosition === 0
          })
          imgPosition++
        }
      }

      // Get clean HTML
      bodyHtml = cleanHtml(contentClone.innerHTML || '')

      // Extract excerpt (first paragraph)
      const firstP = contentClone.querySelector('p')
      if (firstP) {
        excerpt = firstP.textContent?.trim()?.substring(0, 300) || null
      }
    }

    // Calculate word count (Chinese characters + words)
    const plainText = bodyHtml.replace(/<[^>]*>/g, '')
    const wordCount = countWords(plainText)

    return {
      url,
      articleId,
      title,
      authorLine,
      bodyHtml,
      excerpt,
      wordCount,
      category,
      tags,
      publishDate,
      images
    }

  } catch (err) {
    console.error(`Error scraping article detail: ${url}`, err)
    return null
  }
}

// ============================================================
// Helper Functions
// ============================================================

function parseDate(dateText: string): string | null {
  if (!dateText) return null

  // Try ISO format first
  if (/^\d{4}-\d{2}-\d{2}/.test(dateText)) {
    return dateText.substring(0, 10)
  }

  // Chinese format: 2024年12月7日
  const cnMatch = dateText.match(/(\d{4})年(\d{1,2})月(\d{1,2})/)
  if (cnMatch) {
    const [, year, month, day] = cnMatch
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
  }

  // Slash format: 2024/12/7
  const slashMatch = dateText.match(/(\d{4})\/(\d{1,2})\/(\d{1,2})/)
  if (slashMatch) {
    const [, year, month, day] = slashMatch
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
  }

  return null
}

function cleanHtml(html: string): string {
  return html
    // Remove inline styles
    .replace(/\s*style="[^"]*"/gi, '')
    // Remove class attributes (optional, keep for reference)
    // .replace(/\s*class="[^"]*"/gi, '')
    // Remove empty tags
    .replace(/<(\w+)[^>]*>\s*<\/\1>/gi, '')
    // Normalize whitespace
    .replace(/\s+/g, ' ')
    .trim()
}

function countWords(text: string): number {
  // Count Chinese characters
  const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length

  // Count English words
  const englishWords = (text.match(/[a-zA-Z]+/g) || []).length

  return chineseChars + englishWords
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}
