/**
 * Phase 7 Unified AI Optimization E2E Tests
 *
 * Tests for Phase 7 unified optimization service including:
 * - Unified optimization generation (Title + SEO + FAQ in one call)
 * - Step 2 to Step 3 workflow transition
 * - SEO suggestions display and interaction
 * - FAQ generation and display
 * - Caching mechanism
 * - Regeneration functionality
 * - Cost tracking and performance metrics
 * - Monitoring endpoints
 */

import { test, expect, type Page } from '@playwright/test';
import type { APIRequestContext } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.TEST_LOCAL
  ? 'http://localhost:4173/'
  : 'https://storage.googleapis.com/cms-automation-frontend-2025/';

const API_BASE_URL = process.env.TEST_LOCAL
  ? 'http://localhost:8000'
  : 'https://cms-automation-backend-baau2zqeqq-ue.a.run.app';

// Test data
const TEST_ARTICLE_DATA = {
  title: 'Python编程完全指南 - E2E测试',
  body_html: `
    <h2>Python简介</h2>
    <p>Python是一种广泛使用的高级编程语言，以其简洁的语法和强大的功能而闻名。</p>
    <h2>基础语法</h2>
    <p>Python使用缩进来定义代码块，这是其独特的特性之一。变量无需声明类型。</p>
    <h2>数据类型</h2>
    <p>Python支持多种数据类型，包括整数、浮点数、字符串、列表、元组、字典和集合。</p>
    <h2>函数和类</h2>
    <p>Python支持面向对象编程，可以定义类和方法。函数是第一类对象。</p>
    <h2>应用领域</h2>
    <p>Python广泛应用于Web开发、数据分析、人工智能、自动化脚本等领域。</p>
  `.repeat(3), // 重复3次以确保有足够内容
  meta_description: '学习Python编程的基础知识和高级特性',
};

/**
 * Helper: Create a test article via API
 */
async function createTestArticle(request: APIRequestContext): Promise<number> {
  const response = await request.post(`${API_BASE_URL}/v1/articles`, {
    data: {
      title: TEST_ARTICLE_DATA.title,
      body_html: TEST_ARTICLE_DATA.body_html,
      meta_description: TEST_ARTICLE_DATA.meta_description,
      status: 'draft',
    },
  });

  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  return data.id;
}

/**
 * Helper: Simulate Step 1 (parsing) completion
 */
async function completeParsingStep(
  request: APIRequestContext,
  articleId: number
): Promise<void> {
  // Mark article as parsed
  const response = await request.patch(`${API_BASE_URL}/v1/articles/${articleId}`, {
    data: {
      status: 'parsed',
      parsing_confirmed: false,
    },
  });

  expect(response.ok()).toBeTruthy();
}

/**
 * Helper: Confirm parsing (Step 2)
 */
async function confirmParsing(
  request: APIRequestContext,
  articleId: number
): Promise<void> {
  const response = await request.post(
    `${API_BASE_URL}/v1/articles/${articleId}/confirm-parsing`,
    {
      data: {
        confirmed: true,
      },
    }
  );

  expect(response.ok()).toBeTruthy();
}

/**
 * Helper: Generate unified optimizations
 */
async function generateOptimizations(
  request: APIRequestContext,
  articleId: number,
  regenerate: boolean = false
): Promise<any> {
  const response = await request.post(
    `${API_BASE_URL}/v1/articles/${articleId}/generate-all-optimizations`,
    {
      data: {
        regenerate,
        options: {
          include_title: true,
          include_seo: true,
          include_tags: true,
          include_faqs: true,
          faq_target_count: 8,
        },
      },
    }
  );

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Helper: Get cached optimizations
 */
async function getCachedOptimizations(
  request: APIRequestContext,
  articleId: number
): Promise<any> {
  const response = await request.get(
    `${API_BASE_URL}/v1/articles/${articleId}/optimizations`
  );

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Helper: Delete optimizations
 */
async function deleteOptimizations(
  request: APIRequestContext,
  articleId: number
): Promise<void> {
  const response = await request.delete(
    `${API_BASE_URL}/v1/articles/${articleId}/optimizations`
  );

  expect(response.status()).toBe(204);
}

/**
 * Helper: Clean up test article
 */
async function cleanupArticle(
  request: APIRequestContext,
  articleId: number
): Promise<void> {
  await request.delete(`${API_BASE_URL}/v1/articles/${articleId}`);
}

// ============================================================================
// Test Suites
// ============================================================================

test.describe('Phase 7 - Unified Optimization Generation', () => {
  let articleId: number;

  test.beforeEach(async ({ request }) => {
    // Create test article
    articleId = await createTestArticle(request);
    await completeParsingStep(request, articleId);
  });

  test.afterEach(async ({ request }) => {
    // Cleanup
    if (articleId) {
      await cleanupArticle(request, articleId);
    }
  });

  test('should generate all optimizations in a single API call', async ({ request }) => {
    const result = await generateOptimizations(request, articleId);

    // Verify response structure
    expect(result).toHaveProperty('title_suggestions');
    expect(result).toHaveProperty('seo_suggestions');
    expect(result).toHaveProperty('faqs');
    expect(result).toHaveProperty('generation_metadata');

    // Verify title suggestions
    expect(result.title_suggestions.suggested_title_sets).toBeInstanceOf(Array);
    expect(result.title_suggestions.suggested_title_sets.length).toBeGreaterThan(0);
    expect(result.title_suggestions.suggested_title_sets.length).toBeLessThanOrEqual(3);

    // Verify SEO suggestions
    expect(result.seo_suggestions.seo_keywords).toHaveProperty('focus_keyword');
    expect(result.seo_suggestions.seo_keywords).toHaveProperty('primary_keywords');
    expect(result.seo_suggestions.seo_keywords).toHaveProperty('secondary_keywords');
    expect(result.seo_suggestions.meta_description).toHaveProperty('suggested_meta_description');
    expect(result.seo_suggestions.tags).toHaveProperty('suggested_tags');

    // Verify FAQs
    expect(result.faqs).toBeInstanceOf(Array);
    expect(result.faqs.length).toBeGreaterThanOrEqual(3);
    expect(result.faqs.length).toBeLessThanOrEqual(15);

    // Verify each FAQ has required fields
    for (const faq of result.faqs) {
      expect(faq).toHaveProperty('question');
      expect(faq).toHaveProperty('answer');
      expect(faq.question).toBeTruthy();
      expect(faq.answer).toBeTruthy();
    }

    // Verify generation metadata
    expect(result.generation_metadata).toHaveProperty('total_cost_usd');
    expect(result.generation_metadata).toHaveProperty('total_tokens');
    expect(result.generation_metadata).toHaveProperty('input_tokens');
    expect(result.generation_metadata).toHaveProperty('output_tokens');
    expect(result.generation_metadata).toHaveProperty('duration_ms');
    expect(result.generation_metadata.cached).toBe(false);

    // Verify cost is reasonable
    expect(result.generation_metadata.total_cost_usd).toBeGreaterThan(0);
    expect(result.generation_metadata.total_cost_usd).toBeLessThan(0.20); // Should be under $0.20

    // Verify token usage
    expect(result.generation_metadata.total_tokens).toBeGreaterThan(0);
    expect(result.generation_metadata.input_tokens).toBeGreaterThan(0);
    expect(result.generation_metadata.output_tokens).toBeGreaterThan(0);

    console.log(`✅ Generation successful: $${result.generation_metadata.total_cost_usd.toFixed(4)}, ${result.generation_metadata.total_tokens} tokens, ${result.generation_metadata.duration_ms}ms`);
  });

  test('should return cached results on second call', async ({ request }) => {
    // First call: Generate
    const firstResult = await generateOptimizations(request, articleId, false);
    expect(firstResult.generation_metadata.cached).toBe(false);
    const firstCost = firstResult.generation_metadata.total_cost_usd;

    // Second call: Should return cached
    const secondResult = await generateOptimizations(request, articleId, false);
    expect(secondResult.generation_metadata.cached).toBe(true);
    expect(secondResult.generation_metadata.message).toContain('cache');

    // Verify content is the same
    expect(secondResult.title_suggestions).toEqual(firstResult.title_suggestions);
    expect(secondResult.seo_suggestions).toEqual(firstResult.seo_suggestions);
    expect(secondResult.faqs).toEqual(firstResult.faqs);

    console.log(`✅ Cache hit confirmed, saved $${firstCost.toFixed(4)}`);
  });

  test('should regenerate when regenerate flag is true', async ({ request }) => {
    // First call: Generate
    await generateOptimizations(request, articleId, false);

    // Second call: Regenerate
    const result = await generateOptimizations(request, articleId, true);

    // Should NOT be cached
    expect(result.generation_metadata.cached).toBe(false);
    expect(result.generation_metadata.total_cost_usd).toBeGreaterThan(0);

    console.log(`✅ Regeneration successful: $${result.generation_metadata.total_cost_usd.toFixed(4)}`);
  });

  test('should retrieve optimizations via GET endpoint', async ({ request }) => {
    // Generate optimizations first
    await generateOptimizations(request, articleId);

    // Retrieve via GET
    const result = await getCachedOptimizations(request, articleId);

    // Verify response structure
    expect(result).toHaveProperty('title_suggestions');
    expect(result).toHaveProperty('seo_suggestions');
    expect(result).toHaveProperty('faqs');
    expect(result.generation_metadata.cached).toBe(true);

    console.log('✅ GET optimizations successful');
  });

  test('should delete optimizations', async ({ request }) => {
    // Generate optimizations
    await generateOptimizations(request, articleId);

    // Delete
    await deleteOptimizations(request, articleId);

    // Try to retrieve (should fail with 404)
    const response = await request.get(
      `${API_BASE_URL}/v1/articles/${articleId}/optimizations`
    );

    expect(response.status()).toBe(404);

    console.log('✅ Delete optimizations successful');
  });

  test('should check optimization status', async ({ request }) => {
    // Check status before generation
    let statusResponse = await request.get(
      `${API_BASE_URL}/v1/articles/${articleId}/optimization-status`
    );
    expect(statusResponse.ok()).toBeTruthy();
    let status = await statusResponse.json();

    expect(status.generated).toBe(false);
    expect(status.has_title_suggestions).toBe(false);
    expect(status.has_seo_suggestions).toBe(false);
    expect(status.has_faqs).toBe(false);
    expect(status.faq_count).toBe(0);

    // Generate optimizations
    await generateOptimizations(request, articleId);

    // Check status after generation
    statusResponse = await request.get(
      `${API_BASE_URL}/v1/articles/${articleId}/optimization-status`
    );
    status = await statusResponse.json();

    expect(status.generated).toBe(true);
    expect(status.has_title_suggestions).toBe(true);
    expect(status.has_seo_suggestions).toBe(true);
    expect(status.has_faqs).toBe(true);
    expect(status.faq_count).toBeGreaterThan(0);
    expect(status.cost_usd).toBeGreaterThan(0);
    expect(status.generated_at).toBeTruthy();

    console.log(`✅ Status check successful: ${status.faq_count} FAQs, $${status.cost_usd.toFixed(4)}`);
  });
});

test.describe('Phase 7 - SEO and FAQ Content Quality', () => {
  let articleId: number;
  let optimizations: any;

  test.beforeAll(async ({ request }) => {
    // Create and generate optimizations once for all tests
    articleId = await createTestArticle(request);
    await completeParsingStep(request, articleId);
    optimizations = await generateOptimizations(request, articleId);
  });

  test.afterAll(async ({ request }) => {
    if (articleId) {
      await cleanupArticle(request, articleId);
    }
  });

  test('should generate valid title suggestions', () => {
    const titleSets = optimizations.title_suggestions.suggested_title_sets;

    for (const titleOption of titleSets) {
      // Check required fields
      expect(titleOption).toHaveProperty('id');
      expect(titleOption).toHaveProperty('title_main');
      expect(titleOption).toHaveProperty('full_title');
      expect(titleOption).toHaveProperty('score');
      expect(titleOption).toHaveProperty('type');

      // Validate score
      expect(titleOption.score).toBeGreaterThanOrEqual(0);
      expect(titleOption.score).toBeLessThanOrEqual(100);

      // Validate type
      expect(['data_driven', 'authority_backed', 'how_to', 'comprehensive_guide', 'question_based']).toContain(titleOption.type);

      // Validate character counts
      expect(titleOption.character_count).toHaveProperty('total');
      expect(titleOption.character_count.total).toBeGreaterThan(0);
      expect(titleOption.character_count.total).toBeLessThanOrEqual(60); // Reasonable limit

      console.log(`  📝 Title Option: "${titleOption.full_title}" (Score: ${titleOption.score}, Type: ${titleOption.type})`);
    }

    console.log(`✅ ${titleSets.length} title suggestions validated`);
  });

  test('should generate valid SEO keywords', () => {
    const seoKeywords = optimizations.seo_suggestions.seo_keywords;

    // Validate focus keyword
    expect(seoKeywords.focus_keyword).toBeTruthy();
    expect(typeof seoKeywords.focus_keyword).toBe('string');

    // Validate primary keywords
    expect(seoKeywords.primary_keywords).toBeInstanceOf(Array);
    expect(seoKeywords.primary_keywords.length).toBeGreaterThanOrEqual(3);
    expect(seoKeywords.primary_keywords.length).toBeLessThanOrEqual(5);

    // Validate secondary keywords
    expect(seoKeywords.secondary_keywords).toBeInstanceOf(Array);
    expect(seoKeywords.secondary_keywords.length).toBeGreaterThanOrEqual(3);
    expect(seoKeywords.secondary_keywords.length).toBeLessThanOrEqual(10);

    console.log(`  🎯 Focus Keyword: "${seoKeywords.focus_keyword}"`);
    console.log(`  📊 Primary Keywords (${seoKeywords.primary_keywords.length}): ${seoKeywords.primary_keywords.join(', ')}`);
    console.log(`  📋 Secondary Keywords (${seoKeywords.secondary_keywords.length}): ${seoKeywords.secondary_keywords.slice(0, 5).join(', ')}...`);
    console.log('✅ SEO keywords validated');
  });

  test('should generate valid meta description', () => {
    const metaDesc = optimizations.seo_suggestions.meta_description;

    // Validate suggested meta description
    expect(metaDesc.suggested_meta_description).toBeTruthy();
    expect(typeof metaDesc.suggested_meta_description).toBe('string');

    // Validate length (should be 150-160 chars ideally)
    const length = metaDesc.suggested_meta_description.length;
    expect(length).toBeGreaterThan(50);
    expect(length).toBeLessThanOrEqual(200);

    // Validate score if present
    if (metaDesc.meta_description_score !== null) {
      expect(metaDesc.meta_description_score).toBeGreaterThanOrEqual(0);
      expect(metaDesc.meta_description_score).toBeLessThanOrEqual(100);
    }

    console.log(`  📝 Meta Description (${length} chars): "${metaDesc.suggested_meta_description.substring(0, 80)}..."`);
    console.log(`  ⭐ Score: ${metaDesc.meta_description_score || 'N/A'}`);
    console.log('✅ Meta description validated');
  });

  test('should generate valid tags', () => {
    const tags = optimizations.seo_suggestions.tags.suggested_tags;

    // Validate tags array
    expect(tags).toBeInstanceOf(Array);
    expect(tags.length).toBeGreaterThanOrEqual(4);
    expect(tags.length).toBeLessThanOrEqual(10);

    // Validate each tag
    for (const tag of tags) {
      expect(tag).toHaveProperty('tag');
      expect(tag).toHaveProperty('relevance');
      expect(tag).toHaveProperty('type');

      // Validate relevance score
      expect(tag.relevance).toBeGreaterThanOrEqual(0);
      expect(tag.relevance).toBeLessThanOrEqual(1);

      // Validate type
      expect(['primary', 'secondary', 'trending']).toContain(tag.type);
    }

    console.log(`  🏷️  Tags (${tags.length}): ${tags.map(t => `${t.tag} (${t.type})`).join(', ')}`);
    console.log('✅ Tags validated');
  });

  test('should generate valid FAQs', () => {
    const faqs = optimizations.faqs;

    // Validate FAQ array
    expect(faqs.length).toBeGreaterThanOrEqual(3);
    expect(faqs.length).toBeLessThanOrEqual(15);

    // Validate each FAQ
    for (const faq of faqs) {
      // Required fields
      expect(faq.question).toBeTruthy();
      expect(faq.answer).toBeTruthy();
      expect(typeof faq.question).toBe('string');
      expect(typeof faq.answer).toBe('string');

      // Validate question length
      expect(faq.question.length).toBeGreaterThan(5);
      expect(faq.question.length).toBeLessThan(200);

      // Validate answer length
      expect(faq.answer.length).toBeGreaterThan(10);
      expect(faq.answer.length).toBeLessThan(500);

      // Validate question type if present
      if (faq.question_type) {
        expect(['factual', 'how_to', 'comparison', 'definition']).toContain(faq.question_type);
      }

      // Validate search intent if present
      if (faq.search_intent) {
        expect(['informational', 'navigational', 'transactional']).toContain(faq.search_intent);
      }

      // Validate confidence if present
      if (faq.confidence !== null) {
        expect(faq.confidence).toBeGreaterThanOrEqual(0);
        expect(faq.confidence).toBeLessThanOrEqual(1);
      }

      console.log(`  ❓ Q: ${faq.question.substring(0, 50)}...`);
      console.log(`     A: ${faq.answer.substring(0, 80)}...`);
    }

    console.log(`✅ ${faqs.length} FAQs validated`);
  });
});

test.describe('Phase 7 - Monitoring and Cost Tracking', () => {
  test('should get cost statistics', async ({ request }) => {
    const response = await request.get(
      `${API_BASE_URL}/v1/monitoring/optimization/cost-statistics?days=7&limit=50`
    );

    expect(response.ok()).toBeTruthy();
    const stats = await response.json();

    // Validate response structure
    expect(stats).toHaveProperty('period_days');
    expect(stats).toHaveProperty('article_count');
    expect(stats).toHaveProperty('total_cost_usd');
    expect(stats).toHaveProperty('average_cost_usd');
    expect(stats).toHaveProperty('min_cost_usd');
    expect(stats).toHaveProperty('max_cost_usd');
    expect(stats).toHaveProperty('median_cost_usd');
    expect(stats).toHaveProperty('estimated_monthly_cost_usd');

    // Validate data types
    expect(typeof stats.article_count).toBe('number');
    expect(typeof stats.total_cost_usd).toBe('number');
    expect(typeof stats.average_cost_usd).toBe('number');

    console.log(`📊 Cost Statistics (${stats.period_days} days):`);
    console.log(`   Articles: ${stats.article_count}`);
    console.log(`   Total Cost: $${stats.total_cost_usd.toFixed(4)}`);
    console.log(`   Average Cost: $${stats.average_cost_usd.toFixed(4)}`);
    console.log(`   Monthly Estimate: $${stats.estimated_monthly_cost_usd.toFixed(2)}`);
    console.log('✅ Cost statistics retrieved successfully');
  });

  test('should get performance statistics', async ({ request }) => {
    const response = await request.get(
      `${API_BASE_URL}/v1/monitoring/optimization/performance-statistics?days=7`
    );

    expect(response.ok()).toBeTruthy();
    const stats = await response.json();

    // Validate response structure
    expect(stats).toHaveProperty('period_days');
    expect(stats).toHaveProperty('total_optimizations');
    expect(stats).toHaveProperty('cache_hit_rate');
    expect(stats).toHaveProperty('recent_optimizations');

    // Validate data types
    expect(typeof stats.total_optimizations).toBe('number');
    expect(typeof stats.cache_hit_rate).toBe('number');
    expect(stats.recent_optimizations).toBeInstanceOf(Array);

    console.log(`⚡ Performance Statistics (${stats.period_days} days):`);
    console.log(`   Total Optimizations: ${stats.total_optimizations}`);
    console.log(`   Cache Hit Rate: ${stats.cache_hit_rate.toFixed(1)}%`);
    console.log(`   Recent Count: ${stats.recent_optimizations.length}`);
    console.log('✅ Performance statistics retrieved successfully');
  });

  test('should get expensive articles', async ({ request }) => {
    const response = await request.get(
      `${API_BASE_URL}/v1/monitoring/optimization/expensive-articles?days=30&limit=5`
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // Validate response structure
    expect(data).toHaveProperty('period_days');
    expect(data).toHaveProperty('count');
    expect(data).toHaveProperty('articles');
    expect(data.articles).toBeInstanceOf(Array);

    // Validate each article
    for (const article of data.articles) {
      expect(article).toHaveProperty('article_id');
      expect(article).toHaveProperty('title');
      expect(article).toHaveProperty('cost_usd');
      expect(article).toHaveProperty('generated_at');
      expect(article).toHaveProperty('body_length');

      console.log(`  💰 Article #${article.article_id}: "${article.title?.substring(0, 30)}..." - $${article.cost_usd.toFixed(4)}`);
    }

    console.log(`✅ Found ${data.count} expensive articles`);
  });

  test('should get comprehensive monitoring report', async ({ request }) => {
    const response = await request.get(
      `${API_BASE_URL}/v1/monitoring/optimization/report?days=7`
    );

    expect(response.ok()).toBeTruthy();
    const report = await response.json();

    // Validate response structure
    expect(report).toHaveProperty('report_generated_at');
    expect(report).toHaveProperty('period_days');
    expect(report).toHaveProperty('cost_statistics');
    expect(report).toHaveProperty('performance_statistics');
    expect(report).toHaveProperty('top_expensive_articles');
    expect(report).toHaveProperty('summary');

    // Validate summary
    expect(report.summary).toHaveProperty('total_articles_optimized');
    expect(report.summary).toHaveProperty('total_cost_usd');
    expect(report.summary).toHaveProperty('average_cost_per_article');
    expect(report.summary).toHaveProperty('estimated_monthly_cost');
    expect(report.summary).toHaveProperty('cache_hit_rate');

    console.log(`📈 Monitoring Report (${report.period_days} days):`);
    console.log(`   Generated At: ${report.report_generated_at}`);
    console.log(`   Articles Optimized: ${report.summary.total_articles_optimized}`);
    console.log(`   Total Cost: $${report.summary.total_cost_usd.toFixed(4)}`);
    console.log(`   Average Cost: $${report.summary.average_cost_per_article.toFixed(4)}`);
    console.log(`   Cache Hit Rate: ${report.summary.cache_hit_rate.toFixed(1)}%`);
    console.log(`   Monthly Estimate: $${report.summary.estimated_monthly_cost.toFixed(2)}`);
    console.log('✅ Monitoring report retrieved successfully');
  });

  test('should get formatted cost report', async ({ request }) => {
    const response = await request.get(
      `${API_BASE_URL}/v1/monitoring/optimization/cost-report/formatted?days=30&limit=100`
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // Validate response structure
    expect(data).toHaveProperty('report');
    expect(data).toHaveProperty('statistics');

    // Validate report is a non-empty string
    expect(typeof data.report).toBe('string');
    expect(data.report.length).toBeGreaterThan(100);
    expect(data.report).toContain('Cost Statistics Report');
    expect(data.report).toContain('Article Count');
    expect(data.report).toContain('Total Cost');

    console.log('📝 Formatted Report Preview:');
    console.log(data.report.split('\n').slice(0, 10).join('\n'));
    console.log('✅ Formatted cost report retrieved successfully');
  });
});

test.describe('Phase 7 - Error Handling', () => {
  test('should return 404 for non-existent article', async ({ request }) => {
    const response = await request.get(
      `${API_BASE_URL}/v1/articles/999999/optimizations`
    );

    expect(response.status()).toBe(404);

    console.log('✅ 404 error handling verified');
  });

  test('should return 404 for article without optimizations', async ({ request }) => {
    // Create article without generating optimizations
    const articleId = await createTestArticle(request);

    const response = await request.get(
      `${API_BASE_URL}/v1/articles/${articleId}/optimizations`
    );

    expect(response.status()).toBe(404);
    const data = await response.json();
    expect(data.detail).toContain('No optimizations found');

    // Cleanup
    await cleanupArticle(request, articleId);

    console.log('✅ Missing optimizations error handling verified');
  });

  test('should reject invalid optimization options', async ({ request }) => {
    const articleId = await createTestArticle(request);
    await completeParsingStep(request, articleId);

    // Try with invalid faq_target_count
    const response = await request.post(
      `${API_BASE_URL}/v1/articles/${articleId}/generate-all-optimizations`,
      {
        data: {
          regenerate: false,
          options: {
            faq_target_count: 99, // Invalid: max is 15
          },
        },
      }
    );

    expect(response.ok()).toBeFalsy();
    expect(response.status()).toBe(422); // Validation error

    // Cleanup
    await cleanupArticle(request, articleId);

    console.log('✅ Invalid options validation verified');
  });
});

test.describe('Phase 7 - Performance Benchmarks', () => {
  let articleId: number;

  test.beforeAll(async ({ request }) => {
    articleId = await createTestArticle(request);
    await completeParsingStep(request, articleId);
  });

  test.afterAll(async ({ request }) => {
    if (articleId) {
      await cleanupArticle(request, articleId);
    }
  });

  test('should complete generation within performance thresholds', async ({ request }) => {
    const startTime = Date.now();

    const result = await generateOptimizations(request, articleId);

    const endTime = Date.now();
    const clientDuration = endTime - startTime;
    const serverDuration = result.generation_metadata.duration_ms;

    // Performance thresholds
    const MAX_SERVER_DURATION = 35000; // 35 seconds
    const MAX_CLIENT_DURATION = 40000; // 40 seconds (including network)
    const MAX_COST = 0.15; // $0.15

    expect(serverDuration).toBeLessThan(MAX_SERVER_DURATION);
    expect(clientDuration).toBeLessThan(MAX_CLIENT_DURATION);
    expect(result.generation_metadata.total_cost_usd).toBeLessThan(MAX_COST);

    // Token efficiency (should get reasonable tokens per dollar)
    const tokensPerDollar = result.generation_metadata.total_tokens / result.generation_metadata.total_cost_usd;
    expect(tokensPerDollar).toBeGreaterThan(30000); // At least 30k tokens/$

    console.log(`⏱️  Performance Metrics:`);
    console.log(`   Server Duration: ${serverDuration}ms (threshold: ${MAX_SERVER_DURATION}ms)`);
    console.log(`   Client Duration: ${clientDuration}ms (threshold: ${MAX_CLIENT_DURATION}ms)`);
    console.log(`   Cost: $${result.generation_metadata.total_cost_usd.toFixed(4)} (threshold: $${MAX_COST})`);
    console.log(`   Tokens/Dollar: ${tokensPerDollar.toFixed(0)} (threshold: 30000+)`);

    if (serverDuration > 20000) {
      console.warn(`⚠️  Warning: Server duration (${serverDuration}ms) is high but within threshold`);
    }
    if (result.generation_metadata.total_cost_usd > 0.10) {
      console.warn(`⚠️  Warning: Cost ($${result.generation_metadata.total_cost_usd.toFixed(4)}) is high but within threshold`);
    }

    console.log('✅ Performance benchmarks met');
  });

  test('should demonstrate cost savings vs separate calls', async ({ request }) => {
    const result = await generateOptimizations(request, articleId, true);

    // Verify savings data is present
    expect(result.generation_metadata).toHaveProperty('savings_vs_separate');
    const savings = result.generation_metadata.savings_vs_separate;

    if (savings) {
      expect(savings).toHaveProperty('original_cost_usd');
      expect(savings).toHaveProperty('saved_cost_usd');
      expect(savings).toHaveProperty('cost_savings_percentage');
      expect(savings).toHaveProperty('time_savings_percentage');

      // Validate savings are positive
      expect(savings.saved_cost_usd).toBeGreaterThan(0);
      expect(savings.cost_savings_percentage).toBeGreaterThan(0);

      console.log(`💰 Cost Savings Analysis:`);
      console.log(`   Unified Call Cost: $${result.generation_metadata.total_cost_usd.toFixed(4)}`);
      console.log(`   Separate Calls Cost: $${savings.original_cost_usd.toFixed(4)}`);
      console.log(`   Saved: $${savings.saved_cost_usd.toFixed(4)} (${savings.cost_savings_percentage.toFixed(1)}%)`);
      console.log(`   Time Saved: ${savings.saved_duration_ms}ms (${savings.time_savings_percentage.toFixed(1)}%)`);
      console.log('✅ Cost savings validated');
    } else {
      console.log('ℹ️  Savings data not available in this response');
    }
  });
});
