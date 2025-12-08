/**
 * Parse Articles Edge Function (V2)
 *
 * 使用 GPT-4o-mini 進行輕量級 AI 增強解析：
 * ✅ 標題分解（前綴/主標題/副標題）
 * ✅ 作者名清理
 * ✅ 關鍵詞提取（3-5 個）
 * ✅ 分類驗證和推斷
 *
 * ❌ 不做 FAQ 生成（需要深度理解）
 * ❌ 不做深度 SEO 優化（需要搜索意圖分析）
 * ❌ 不做內容校對（需要專家模型）
 *
 * @version 2.0
 * @date 2025-12-07
 */

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// ============================================================
// Configuration
// ============================================================

const BATCH_SIZE = 10 // 每批處理文章數
const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'
const MODEL = 'gpt-4o-mini'

// 有效的健康分類
const VALID_CATEGORIES = [
  '健康養生',
  '食療養生',
  '健康生活',
  '疾病預防',
  '心理健康',
  '運動健身',
  '中醫養生',
  '營養保健'
]

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
}

// ============================================================
// System Prompt - 明確限制 AI 能做什麼
// ============================================================

const SYSTEM_PROMPT = `你是一個健康文章結構化解析專家。

## 你的任務（只做這些）：
1. **標題分解**：將標題拆分為前綴、主標題、副標題
2. **作者清理**：從作者行提取乾淨的作者名
3. **關鍵詞提取**：提取 3-5 個健康領域關鍵詞
4. **分類驗證**：確認或修正文章分類

## 你不應該做（會誤導用戶）：
- ❌ 不要生成 FAQ
- ❌ 不要生成 SEO 優化建議
- ❌ 不要校對或修改內容
- ❌ 不要創作新內容

## 標題分解規則：
- 前綴：【】或[]包裹的部分，如【專題】【健康1+1】
- 主標題：核心標題內容
- 副標題：用「——」「：」「|」分隔的後半部分

## 關鍵詞提取規則：
- 3-5 個關鍵詞
- 優先：疾病名稱、症狀、治療方法、食材、健康主題
- 使用繁體中文
- 每個關鍵詞 1-4 個字

## 分類選項：
${VALID_CATEGORIES.map(c => `- ${c}`).join('\n')}

## 輸出格式（JSON 對象，包含 results 數組）：
{
  "results": [
    {
      "article_id": "n12345678",
      "title_prefix": "【專題】",
      "title_main": "主標題",
      "title_suffix": "副標題或 null",
      "author_name": "清理後的作者名或 null",
      "ai_keywords": ["關鍵詞1", "關鍵詞2", "關鍵詞3"],
      "primary_category": "健康養生",
      "secondary_categories": ["食療養生"]
    }
  ]
}`

// ============================================================
// Types
// ============================================================

interface ArticleInput {
  article_id: string
  title: string
  author_line: string | null
  category: string
  original_tags: string[]
  excerpt: string | null
}

interface ParsedResult {
  article_id: string
  title_prefix: string | null
  title_main: string
  title_suffix: string | null
  author_name: string | null
  ai_keywords: string[]
  primary_category: string
  secondary_categories: string[]
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
    const openaiKey = Deno.env.get('OPENAI_API_KEY')

    if (!supabaseUrl || !supabaseKey) {
      throw new Error('Missing Supabase configuration')
    }
    if (!openaiKey) {
      throw new Error('Missing OpenAI API key')
    }

    const supabase = createClient(supabaseUrl, supabaseKey)

    // Parse request options
    const body = await req.json().catch(() => ({}))
    const batchSize = body.batchSize || BATCH_SIZE

    // Get articles that need parsing (status = 'scraped')
    const { data: articles, error: fetchError } = await supabase
      .from('health_articles')
      .select('id, article_id, title, author_line, category, original_tags, excerpt')
      .eq('status', 'scraped')
      .limit(batchSize)

    if (fetchError) {
      throw new Error(`Failed to fetch articles: ${fetchError.message}`)
    }

    if (!articles || articles.length === 0) {
      return new Response(
        JSON.stringify({
          success: true,
          processed: 0,
          message: 'No articles pending parsing'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Create job record
    const { data: job } = await supabase
      .from('scrape_jobs')
      .insert({
        job_type: 'parse',
        metadata: { batchSize, articleCount: articles.length }
      })
      .select()
      .single()

    console.log(`Processing ${articles.length} articles for AI parsing`)

    // Build input for OpenAI
    const articlesInput: ArticleInput[] = articles.map(a => ({
      article_id: a.article_id,
      title: a.title,
      author_line: a.author_line,
      category: a.category,
      original_tags: a.original_tags || [],
      excerpt: a.excerpt?.substring(0, 200) || null
    }))

    const userPrompt = `請解析以下 ${articles.length} 篇健康文章：

${JSON.stringify(articlesInput, null, 2)}`

    // Call OpenAI API
    const openaiResponse = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${openaiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.2, // 低溫度確保穩定輸出
        max_tokens: 4000,
        response_format: { type: 'json_object' }
      })
    })

    if (!openaiResponse.ok) {
      const errorData = await openaiResponse.json()
      throw new Error(`OpenAI API error: ${errorData.error?.message || 'Unknown error'}`)
    }

    const openaiResult = await openaiResponse.json()
    const content = openaiResult.choices[0]?.message?.content

    if (!content) {
      throw new Error('Empty response from OpenAI')
    }

    // Parse response
    let parsedResults: ParsedResult[]
    try {
      const parsed = JSON.parse(content)
      // Handle both array and object with results array
      parsedResults = Array.isArray(parsed) ? parsed : (parsed.results || parsed.articles || [])
    } catch (e) {
      console.error('Failed to parse OpenAI response:', content)
      throw new Error(`Failed to parse OpenAI response: ${e.message}`)
    }

    // Update articles
    let processed = 0
    let failed = 0
    const errors: string[] = []

    for (const article of articles) {
      const result = parsedResults.find(r => r.article_id === article.article_id)

      if (!result) {
        console.warn(`No parse result for article ${article.article_id}`)
        failed++
        errors.push(`No result: ${article.article_id}`)
        continue
      }

      // Validate and clean keywords
      const validKeywords = Array.isArray(result.ai_keywords)
        ? result.ai_keywords.filter(k => typeof k === 'string' && k.length > 0 && k.length <= 10)
        : []

      // Validate primary category
      const primaryCategory = VALID_CATEGORIES.includes(result.primary_category)
        ? result.primary_category
        : article.category

      // Validate secondary categories
      const secondaryCategories = Array.isArray(result.secondary_categories)
        ? result.secondary_categories.filter(c => VALID_CATEGORIES.includes(c) && c !== primaryCategory)
        : []

      const { error: updateError } = await supabase
        .from('health_articles')
        .update({
          title_prefix: result.title_prefix || null,
          title_main: result.title_main || article.title,
          title_suffix: result.title_suffix || null,
          author_name: result.author_name || null,
          ai_keywords: validKeywords,
          primary_category: primaryCategory,
          secondary_categories: secondaryCategories,
          status: 'parsed',
          parsed_at: new Date().toISOString()
        })
        .eq('id', article.id)

      if (updateError) {
        console.error(`Failed to update article ${article.article_id}:`, updateError)
        failed++
        errors.push(`Update failed: ${article.article_id}`)
      } else {
        processed++
        console.log(`✓ Parsed: ${article.article_id} - ${validKeywords.join(', ')}`)
      }
    }

    // Calculate cost
    const usage = openaiResult.usage || {}
    // GPT-4o-mini: $0.15/1M input, $0.60/1M output
    const inputCost = (usage.prompt_tokens || 0) * 0.00000015
    const outputCost = (usage.completion_tokens || 0) * 0.0000006
    const totalCost = inputCost + outputCost

    // Update job record
    if (job) {
      await supabase
        .from('scrape_jobs')
        .update({
          completed_at: new Date().toISOString(),
          articles_processed: processed,
          articles_failed: failed,
          status: 'completed',
          error_message: errors.length > 0 ? errors.slice(0, 5).join('; ') : null,
          metadata: {
            batchSize,
            articleCount: articles.length,
            tokensUsed: usage.total_tokens,
            estimatedCost: totalCost.toFixed(6)
          }
        })
        .eq('id', job.id)
    }

    return new Response(
      JSON.stringify({
        success: true,
        processed,
        failed,
        tokensUsed: usage.total_tokens,
        estimatedCost: `$${totalCost.toFixed(6)}`,
        jobId: job?.id,
        // 明確標記 AI 功能限制
        aiFeatures: {
          keywords: 'available',
          title_decomposition: 'available',
          category_inference: 'available',
          faq_generation: 'not_available - requires Claude model',
          deep_seo: 'not_available - requires advanced analysis',
          proofreading: 'not_available - requires expert model'
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Parsing error:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
