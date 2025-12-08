/**
 * Generate Embeddings Edge Function (V2)
 *
 * 使用 OpenAI text-embedding-3-small 生成向量嵌入：
 * - 標題向量：用於快速相似度匹配
 * - 正文向量（可選）：用於深度內容匹配
 *
 * @version 2.0
 * @date 2025-12-07
 */

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// ============================================================
// Configuration
// ============================================================

const BATCH_SIZE = 30 // 每批處理文章數
const OPENAI_EMBEDDING_URL = 'https://api.openai.com/v1/embeddings'
const MODEL = 'text-embedding-3-small'
const DIMENSIONS = 1536

// 正文截斷長度（embedding 模型有 token 限制）
const MAX_CONTENT_LENGTH = 8000 // 約 2000 tokens

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
}

// ============================================================
// Types
// ============================================================

interface EmbeddingData {
  embedding: number[]
  index: number
}

interface ArticleForEmbedding {
  id: number
  article_id: string
  title: string
  title_main: string | null
  ai_keywords: string[]
  excerpt: string | null
  body_html: string | null
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
    const includeContentEmbedding = body.includeContent ?? false // 是否生成正文向量

    // Get articles that need embeddings (status = 'parsed')
    const { data: articles, error: fetchError } = await supabase
      .from('health_articles')
      .select('id, article_id, title, title_main, ai_keywords, excerpt, body_html')
      .eq('status', 'parsed')
      .limit(batchSize)

    if (fetchError) {
      throw new Error(`Failed to fetch articles: ${fetchError.message}`)
    }

    if (!articles || articles.length === 0) {
      return new Response(
        JSON.stringify({
          success: true,
          processed: 0,
          message: 'No articles pending embedding generation'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Create job record
    const { data: job } = await supabase
      .from('scrape_jobs')
      .insert({
        job_type: 'embedding',
        metadata: { batchSize, articleCount: articles.length, includeContentEmbedding }
      })
      .select()
      .single()

    console.log(`Generating embeddings for ${articles.length} articles (includeContent: ${includeContentEmbedding})`)

    // ===== Phase 1: Generate Title Embeddings =====
    const titleInputs = articles.map(article => {
      // 使用分解後的主標題（如果有）+ 關鍵詞
      const mainTitle = article.title_main || article.title
      const keywords = article.ai_keywords?.join(', ') || ''
      return keywords ? `${mainTitle} | ${keywords}` : mainTitle
    })

    console.log('Generating title embeddings...')
    const titleEmbeddings = await generateEmbeddings(openaiKey, titleInputs)

    if (!titleEmbeddings || titleEmbeddings.length !== articles.length) {
      throw new Error(`Title embedding count mismatch: expected ${articles.length}, got ${titleEmbeddings?.length || 0}`)
    }

    // ===== Phase 2: Generate Content Embeddings (Optional) =====
    let contentEmbeddings: EmbeddingData[] | null = null

    if (includeContentEmbedding) {
      const contentInputs = articles.map(article => {
        // 使用摘要 + 正文前部分
        let content = article.excerpt || ''

        if (article.body_html) {
          // 移除 HTML 標籤，獲取純文本
          const plainText = article.body_html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
          content = content ? `${content} ${plainText}` : plainText
        }

        // 截斷到最大長度
        return content.substring(0, MAX_CONTENT_LENGTH)
      })

      console.log('Generating content embeddings...')
      contentEmbeddings = await generateEmbeddings(openaiKey, contentInputs)
    }

    // ===== Phase 3: Update Database =====
    let processed = 0
    let failed = 0
    const errors: string[] = []

    for (let i = 0; i < articles.length; i++) {
      const article = articles[i]
      const titleEmb = titleEmbeddings.find(e => e.index === i)

      if (!titleEmb) {
        console.error(`Missing title embedding for article ${article.article_id} at index ${i}`)
        failed++
        errors.push(`No title embedding: ${article.article_id}`)
        continue
      }

      const updateData: Record<string, any> = {
        title_embedding: titleEmb.embedding,
        embedded_at: new Date().toISOString(),
        status: 'ready'
      }

      // Add content embedding if available
      if (contentEmbeddings) {
        const contentEmb = contentEmbeddings.find(e => e.index === i)
        if (contentEmb) {
          updateData.content_embedding = contentEmb.embedding
        }
      }

      const { error: updateError } = await supabase
        .from('health_articles')
        .update(updateData)
        .eq('id', article.id)

      if (updateError) {
        console.error(`Failed to update article ${article.article_id}:`, updateError)
        failed++
        errors.push(`Update failed: ${article.article_id}`)
      } else {
        processed++
        console.log(`✓ Embedded: ${article.article_id}`)
      }
    }

    // Calculate token usage and cost
    // Note: We need to track this manually since we made 1-2 API calls
    const totalTokens = titleInputs.reduce((sum, text) => sum + estimateTokens(text), 0)
      + (includeContentEmbedding ? articles.reduce((sum, a) => sum + estimateTokens(a.excerpt || '') + estimateTokens((a.body_html || '').substring(0, MAX_CONTENT_LENGTH)), 0) : 0)

    // text-embedding-3-small: $0.02 per 1M tokens
    const totalCost = totalTokens * 0.00000002

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
            includeContentEmbedding,
            estimatedTokens: totalTokens,
            estimatedCost: totalCost.toFixed(8)
          }
        })
        .eq('id', job.id)
    }

    return new Response(
      JSON.stringify({
        success: true,
        processed,
        failed,
        estimatedTokens: totalTokens,
        estimatedCost: `$${totalCost.toFixed(8)}`,
        includeContentEmbedding,
        jobId: job?.id
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Embedding generation error:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

// ============================================================
// Helper Functions
// ============================================================

async function generateEmbeddings(apiKey: string, inputs: string[]): Promise<EmbeddingData[]> {
  const response = await fetch(OPENAI_EMBEDDING_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      input: inputs,
      dimensions: DIMENSIONS
    })
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(`OpenAI API error: ${errorData.error?.message || 'Unknown error'}`)
  }

  const result = await response.json()
  return result.data as EmbeddingData[]
}

function estimateTokens(text: string): number {
  // 粗略估計：中文約 2 字符/token，英文約 4 字符/token
  const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length
  const otherChars = text.length - chineseChars

  return Math.ceil(chineseChars / 2 + otherChars / 4)
}
