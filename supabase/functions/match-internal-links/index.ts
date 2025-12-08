/**
 * Match Internal Links Edge Function (V2)
 *
 * 為文章找出相關的內部鏈接推薦，使用混合匹配策略：
 * 1. 標題向量語義匹配（主要）
 * 2. 正文向量深度匹配（可選）
 * 3. 關鍵詞匹配（備選）
 *
 * V2 變更：
 * - 支持 content embedding 深度匹配
 * - 返回更多字段（title_main, excerpt, ai_keywords）
 * - 三層匹配策略
 *
 * @version 2.0
 * @date 2025-12-07
 */

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// ============================================================
// Configuration
// ============================================================

const OPENAI_EMBEDDING_URL = 'https://api.openai.com/v1/embeddings'
const MODEL = 'text-embedding-3-small'
const DIMENSIONS = 1536
const DEFAULT_MATCH_COUNT = 5
const DEFAULT_TITLE_THRESHOLD = 0.7
const DEFAULT_CONTENT_THRESHOLD = 0.6

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
}

// ============================================================
// Types
// ============================================================

interface MatchRequest {
  // 必填：標題用於生成查詢向量
  title: string

  // 可選：增強匹配的附加信息
  keywords?: string[]
  content?: string  // 正文片段，用於深度匹配

  // 過濾選項
  article_id?: string  // 排除此文章（避免自己匹配自己）
  category?: string    // 僅匹配特定分類

  // 匹配控制
  limit?: number
  title_threshold?: number   // 標題相似度閾值
  content_threshold?: number // 正文相似度閾值
  include_content_match?: boolean // 是否啟用正文深度匹配
}

interface MatchResult {
  article_id: string
  title: string
  title_main: string | null
  url: string
  excerpt: string | null
  ai_keywords: string[]
  similarity: number
  match_type: 'semantic' | 'content' | 'keyword'
  matched_keywords?: string[]
}

// ============================================================
// Main Handler
// ============================================================

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get environment variables
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

    // Parse request
    const body: MatchRequest = await req.json()

    if (!body.title || body.title.trim().length === 0) {
      return new Response(
        JSON.stringify({
          success: false,
          error: 'Title is required'
        }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    const {
      title,
      keywords = [],
      content = null,
      article_id: excludeArticleId = null,
      category = null,
      limit = DEFAULT_MATCH_COUNT,
      title_threshold = DEFAULT_TITLE_THRESHOLD,
      content_threshold = DEFAULT_CONTENT_THRESHOLD,
      include_content_match = false
    } = body

    const results: MatchResult[] = []
    const existingIds = new Set<string>()
    let totalTokensUsed = 0

    // ===== Phase 1: Title Semantic Matching =====
    console.log('Phase 1: Title semantic matching...')

    const titleEmbeddingInput = keywords.length > 0
      ? `${title} | ${keywords.join(', ')}`
      : title

    const titleEmbedding = await generateEmbedding(openaiKey, titleEmbeddingInput)
    totalTokensUsed += estimateTokens(titleEmbeddingInput)

    const { data: semanticMatches, error: semanticError } = await supabase
      .rpc('match_health_articles', {
        query_embedding: titleEmbedding,
        match_threshold: title_threshold,
        match_count: limit,
        exclude_article_id: excludeArticleId
      })

    if (semanticError) {
      console.error('Semantic search error:', semanticError)
    } else if (semanticMatches && semanticMatches.length > 0) {
      console.log(`Found ${semanticMatches.length} semantic matches`)

      for (const match of semanticMatches) {
        existingIds.add(match.article_id)
        results.push({
          article_id: match.article_id,
          title: match.title,
          title_main: match.title_main,
          url: match.original_url,
          excerpt: match.excerpt,
          ai_keywords: match.ai_keywords || [],
          similarity: Math.round(match.similarity * 100) / 100,
          match_type: 'semantic'
        })
      }
    }

    // ===== Phase 2: Content Deep Matching (Optional) =====
    if (include_content_match && content && results.length < limit) {
      console.log('Phase 2: Content deep matching...')

      const contentEmbeddingInput = content.substring(0, 8000) // 截斷到約 2000 tokens
      const contentEmbedding = await generateEmbedding(openaiKey, contentEmbeddingInput)
      totalTokensUsed += estimateTokens(contentEmbeddingInput)

      const remainingCount = limit - results.length

      const { data: contentMatches, error: contentError } = await supabase
        .rpc('match_by_content', {
          query_embedding: contentEmbedding,
          match_threshold: content_threshold,
          match_count: remainingCount + 5, // 多取一些以過濾重複
          exclude_article_id: excludeArticleId
        })

      if (contentError) {
        console.error('Content search error:', contentError)
      } else if (contentMatches && contentMatches.length > 0) {
        console.log(`Found ${contentMatches.length} content matches`)

        for (const match of contentMatches) {
          if (existingIds.has(match.article_id)) continue

          existingIds.add(match.article_id)
          results.push({
            article_id: match.article_id,
            title: match.title,
            title_main: null, // match_by_content 不返回 title_main
            url: match.original_url,
            excerpt: match.excerpt,
            ai_keywords: [],
            similarity: Math.round(match.similarity * 100) / 100,
            match_type: 'content'
          })

          if (results.length >= limit) break
        }
      }
    }

    // ===== Phase 3: Keyword Fallback Matching =====
    if (results.length < limit && keywords.length > 0) {
      console.log('Phase 3: Keyword fallback matching...')

      const remainingCount = limit - results.length

      const { data: keywordMatches, error: keywordError } = await supabase
        .rpc('match_by_keywords', {
          source_keywords: keywords,
          match_count: remainingCount + 5,
          exclude_article_id: excludeArticleId
        })

      if (keywordError) {
        console.error('Keyword search error:', keywordError)
      } else if (keywordMatches && keywordMatches.length > 0) {
        console.log(`Found ${keywordMatches.length} keyword matches`)

        for (const match of keywordMatches) {
          if (existingIds.has(match.article_id)) continue

          // 將關鍵詞匹配分數歸一化到 0-1（假設最多 5 個關鍵詞匹配）
          const normalizedScore = Math.min(match.match_score / 5, 1)

          existingIds.add(match.article_id)
          results.push({
            article_id: match.article_id,
            title: match.title,
            title_main: match.title_main,
            url: match.original_url,
            excerpt: null,
            ai_keywords: [],
            similarity: Math.round(normalizedScore * 100) / 100,
            match_type: 'keyword',
            matched_keywords: match.matched_keywords
          })

          if (results.length >= limit) break
        }
      }
    }

    // ===== Final Processing =====
    // 按相似度排序並限制數量
    results.sort((a, b) => b.similarity - a.similarity)
    const finalResults = results.slice(0, limit)

    // 計算成本
    // text-embedding-3-small: $0.02 per 1M tokens
    const embeddingCost = totalTokensUsed * 0.00000002

    // 統計各類型匹配數量
    const stats = {
      totalMatches: finalResults.length,
      semanticMatches: finalResults.filter(r => r.match_type === 'semantic').length,
      contentMatches: finalResults.filter(r => r.match_type === 'content').length,
      keywordMatches: finalResults.filter(r => r.match_type === 'keyword').length,
      tokensUsed: totalTokensUsed,
      estimatedCost: `$${embeddingCost.toFixed(8)}`
    }

    return new Response(
      JSON.stringify({
        success: true,
        matches: finalResults,
        query: {
          title: title.substring(0, 100),
          keywords,
          hasContent: !!content,
          excludeArticleId,
          category
        },
        stats
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Match error:', error)

    return new Response(
      JSON.stringify({
        success: false,
        error: error.message || 'Unknown error occurred'
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

// ============================================================
// Helper Functions
// ============================================================

async function generateEmbedding(apiKey: string, input: string): Promise<number[]> {
  const response = await fetch(OPENAI_EMBEDDING_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      input,
      dimensions: DIMENSIONS
    })
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(`OpenAI API error: ${errorData.error?.message || 'Unknown error'}`)
  }

  const result = await response.json()
  const embedding = result.data[0]?.embedding

  if (!embedding) {
    throw new Error('Failed to generate embedding')
  }

  return embedding
}

function estimateTokens(text: string): number {
  // 粗略估計：中文約 2 字符/token，英文約 4 字符/token
  const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length
  const otherChars = text.length - chineseChars

  return Math.ceil(chineseChars / 2 + otherChars / 4)
}
