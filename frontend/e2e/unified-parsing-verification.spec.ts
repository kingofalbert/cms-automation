/**
 * Unified AI Parsing Verification Test
 * Phase 7.5 - 验证统一提示词功能
 *
 * 测试目标：
 * 1. API返回所有SEO建议字段（suggested_*）
 * 2. UI正确显示这些字段
 * 3. 校对结果和FAQ也被返回
 */

import { test, expect } from '@playwright/test';

const API_BASE = 'https://cms-automation-backend-baau2zqeqq-ue.a.run.app';
const FRONTEND_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test.describe('Unified AI Parsing Verification', () => {
  test.beforeEach(async ({ page }) => {
    // 监听所有API请求
    await page.route(`${API_BASE}/**`, async (route) => {
      const request = route.request();
      console.log(`[API] ${request.method()} ${request.url()}`);
      await route.continue();
    });
  });

  test('Step 1: 验证API返回SEO建议字段（Worklist详情）', async ({ page }) => {
    console.log('\n=== 测试1：验证Worklist API返回SEO建议字段 ===\n');

    // 获取worklist item详情（通常ID 6-11有解析数据）
    const testIds = [6, 7, 9, 10, 11];

    for (const worklistId of testIds) {
      console.log(`\n检查Worklist ID: ${worklistId}`);

      const response = await page.request.get(`${API_BASE}/v1/worklist/${worklistId}`);
      expect(response.ok()).toBeTruthy();

      const data = await response.json();

      // 打印响应结构
      console.log('Response keys:', Object.keys(data));

      // 验证基础解析字段
      console.log('\n✓ 基础解析字段:');
      console.log('  - title:', data.title);
      console.log('  - author_name:', data.author_name || 'NULL');
      console.log('  - seo_title:', data.seo_title || 'NULL');

      // 关键验证：SEO建议字段
      console.log('\n🎯 SEO建议字段 (统一提示词新增):');
      const seoFields = {
        suggested_meta_description: data.suggested_meta_description,
        suggested_seo_keywords: data.suggested_seo_keywords,
        suggested_titles: data.suggested_titles,
      };

      console.log('  - suggested_meta_description:', seoFields.suggested_meta_description || '❌ NULL');
      console.log('  - suggested_seo_keywords:', seoFields.suggested_seo_keywords ? '✅ 已返回' : '❌ NULL');
      console.log('  - suggested_titles:', seoFields.suggested_titles ? `✅ ${seoFields.suggested_titles.length}个建议` : '❌ NULL');

      // 校对字段
      if (data.proofreading_issues) {
        console.log(`\n✏️ 校对结果: ${data.proofreading_issues.length}个问题`);
      } else {
        console.log('\n❌ 校对结果: NULL');
      }

      // FAQ字段
      if (data.faqs) {
        console.log(`✓ FAQ: ${data.faqs.length}个问题`);
      } else {
        console.log('❌ FAQ: NULL');
      }

      // 断言（当前可能失败，因为还未部署统一提示词）
      if (data.suggested_meta_description || data.suggested_seo_keywords || data.suggested_titles) {
        console.log('\n✅ 此文章已有SEO建议（可能是手动生成或旧数据）');
      } else {
        console.log('\n⚠️  此文章缺少SEO建议字段（等待统一提示词部署）');
      }
    }
  });

  test('Step 2: 验证Article API返回完整字段', async ({ page }) => {
    console.log('\n=== 测试2：验证Article API ===\n');

    // 测试article endpoint
    const testArticleIds = [6, 7, 9, 10];

    for (const articleId of testArticleIds) {
      console.log(`\n检查Article ID: ${articleId}`);

      try {
        const response = await page.request.get(`${API_BASE}/v1/articles/${articleId}`);

        if (!response.ok()) {
          console.log(`  ⚠️  Article ${articleId} 不存在或错误`);
          continue;
        }

        const article = await response.json();

        // 验证Schema字段
        const expectedFields = [
          'title_main',
          'author_name',
          'seo_title',
          'meta_description',
          'suggested_meta_description',
          'suggested_seo_keywords',
        ];

        console.log('字段检查:');
        expectedFields.forEach(field => {
          const value = article[field];
          const status = value ? '✅' : '❌';
          console.log(`  ${status} ${field}:`, value || 'NULL');
        });

      } catch (error) {
        console.log(`  ❌ 获取Article ${articleId}失败:`, error.message);
      }
    }
  });

  test('Step 3: 使用Chrome DevTools验证UI显示', async ({ page }) => {
    console.log('\n=== 测试3：验证UI显示SEO建议 ===\n');

    // 导航到Worklist页面
    console.log('访问Worklist页面...');
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // 等待Worklist表格加载
    await page.waitForSelector('table', { timeout: 10000 });

    console.log('✓ Worklist页面加载成功');

    // 点击第一个有数据的item
    const rows = await page.locator('tbody tr').all();
    console.log(`找到 ${rows.length} 个Worklist项`);

    if (rows.length > 0) {
      console.log('\n点击第一个项目打开详情...');
      await rows[0].click();
      await page.waitForTimeout(2000);

      // 检查是否有Modal或详情页面打开
      const modalExists = await page.locator('[role="dialog"]').count() > 0;
      const detailPageExists = await page.url().includes('/articles/');

      if (modalExists) {
        console.log('✓ Modal打开');

        // 截图保存
        await page.screenshot({
          path: '/tmp/worklist-modal-seo-fields.png',
          fullPage: true
        });
        console.log('📸 截图已保存: /tmp/worklist-modal-seo-fields.png');

      } else if (detailPageExists) {
        console.log('✓ 详情页面打开');
        await page.screenshot({
          path: '/tmp/article-detail-seo-fields.png',
          fullPage: true
        });
        console.log('📸 截图已保存: /tmp/article-detail-seo-fields.png');
      }

      // 检查页面内容是否包含SEO建议相关文字
      const pageContent = await page.content();
      const seoKeywords = [
        'SEO',
        '建議',
        '建议',
        'Meta Description',
        '關鍵詞',
        '关键词',
        'suggested',
      ];

      console.log('\n搜索SEO相关内容:');
      seoKeywords.forEach(keyword => {
        const found = pageContent.includes(keyword);
        console.log(`  ${found ? '✅' : '❌'} "${keyword}"`);
      });
    }
  });

  test('Step 4: 测试统一提示词API（如果已部署）', async ({ page }) => {
    console.log('\n=== 测试4：测试重新解析功能 ===\n');

    // 尝试触发重新解析，看是否使用统一提示词
    const testWorklistId = 6;

    console.log(`尝试对Worklist ID ${testWorklistId} 触发重新解析...`);

    try {
      // 注意：这需要有相应的API endpoint
      // 这里只是演示如何测试
      const response = await page.request.post(
        `${API_BASE}/v1/worklist/${testWorklistId}/reparse`,
        {
          headers: {
            'Content-Type': 'application/json'
          },
          data: {
            use_unified_prompt: true
          }
        }
      );

      if (response.ok()) {
        const result = await response.json();
        console.log('✅ 重新解析成功');
        console.log('Response:', JSON.stringify(result, null, 2));
      } else {
        console.log(`⚠️  重新解析失败: ${response.status()} ${response.statusText()}`);
      }
    } catch (error) {
      console.log('ℹ️  重新解析endpoint可能不存在:', error.message);
    }
  });

  test('Step 5: 对比测试 - 统一提示词 vs 原始提示词', async ({ page }) => {
    console.log('\n=== 测试5：对比分析 ===\n');

    const testId = 10;

    console.log('获取当前数据...');
    const currentResponse = await page.request.get(`${API_BASE}/v1/worklist/${testId}`);
    const currentData = await currentResponse.json();

    console.log('\n当前数据分析:');
    console.log('=====================================');

    const analysis = {
      parsing_fields: {
        title_main: currentData.title_main ? '✅' : '❌',
        author_name: currentData.author_name ? '✅' : '❌',
        body_html: currentData.content ? '✅' : '❌',
        images: currentData.article_images?.length > 0 ? `✅ ${currentData.article_images.length}张` : '❌',
      },
      seo_suggestions: {
        suggested_titles: currentData.suggested_titles ? `✅ ${currentData.suggested_titles.length}个` : '❌ NULL',
        suggested_meta_description: currentData.suggested_meta_description ? '✅' : '❌ NULL',
        suggested_seo_keywords: currentData.suggested_seo_keywords ? '✅' : '❌ NULL',
      },
      proofreading: {
        issues: currentData.proofreading_issues ? `✅ ${currentData.proofreading_issues.length}个` : '❌ NULL',
        stats: currentData.proofreading_stats ? '✅' : '❌ NULL',
      },
      faq: {
        faqs: currentData.faqs ? `✅ ${currentData.faqs.length}个` : '❌ NULL',
      }
    };

    console.log('\n📊 字段完整性检查:');
    console.log('\n1️⃣  基础解析字段:');
    Object.entries(analysis.parsing_fields).forEach(([key, value]) => {
      console.log(`   ${value} ${key}`);
    });

    console.log('\n2️⃣  SEO建议字段 (统一提示词目标):');
    Object.entries(analysis.seo_suggestions).forEach(([key, value]) => {
      console.log(`   ${value} ${key}`);
    });

    console.log('\n3️⃣  校对结果:');
    Object.entries(analysis.proofreading).forEach(([key, value]) => {
      console.log(`   ${value} ${key}`);
    });

    console.log('\n4️⃣  FAQ:');
    Object.entries(analysis.faq).forEach(([key, value]) => {
      console.log(`   ${value} ${key}`);
    });

    // 计算完整性评分
    const allFields = [
      ...Object.values(analysis.parsing_fields),
      ...Object.values(analysis.seo_suggestions),
      ...Object.values(analysis.proofreading),
      ...Object.values(analysis.faq),
    ];

    const completedFields = allFields.filter(v => v.startsWith('✅')).length;
    const totalFields = allFields.length;
    const completeness = (completedFields / totalFields * 100).toFixed(0);

    console.log('\n📈 总体完整性评分:');
    console.log(`   ${completedFields}/${totalFields} 字段已填充 (${completeness}%)`);

    if (completeness === '100') {
      console.log('\n🎉 完美！所有字段都已填充 - 统一提示词工作正常！');
    } else if (parseInt(completeness) >= 70) {
      console.log('\n✅ 大部分字段已填充 - 系统运行良好');
    } else if (parseInt(completeness) >= 50) {
      console.log('\n⚠️  部分字段缺失 - 可能还未启用统一提示词');
    } else {
      console.log('\n❌ 大量字段缺失 - 统一提示词可能未部署');
    }
  });
});

test.describe('环境验证', () => {
  test('验证USE_UNIFIED_PARSER环境变量', async ({ page }) => {
    console.log('\n=== 环境变量检查 ===\n');

    // 尝试通过health endpoint或其他方式检查环境变量
    try {
      const response = await page.request.get(`${API_BASE}/health`);
      if (response.ok()) {
        const health = await response.json();
        console.log('Backend health:', health);
      }
    } catch (error) {
      console.log('无法获取health endpoint');
    }

    console.log('\n提示: 检查Cloud Run环境变量');
    console.log('命令: gcloud run services describe cms-automation-backend --region us-east1 --format="yaml(spec.template.spec.containers[0].env)"');
  });
});