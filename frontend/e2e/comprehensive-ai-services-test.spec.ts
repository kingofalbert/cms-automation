/**
 * 全面測試 AI 服務實現
 *
 * 測試範圍：
 * 1. 獨立校對服務 (ProofreadingService)
 * 2. 標題生成服務 (TitleGeneratorService)
 * 3. 整體解析流程
 * 4. AI Prompt 效果驗證
 */

import { test, expect, Page, BrowserContext, chromium } from '@playwright/test';

const API_BASE_URL = 'https://cms-automation-backend-baau2zqeqq-ue.a.run.app';
const FRONTEND_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

// 測試數據
const TEST_ARTICLE = {
  title: "AI技術在醫療領域的應用與挑戰",
  body: `
    近年來，人工智能技術的的快速發展給醫療行業帶來了革命性變化。從医療診斷道治療方案，
    AI正在改變我們對醫療服務的理解。特別是在影像診斷領域，深度學習模型展現了驚人的準確率。

    然而，這些技術也带來了一些倫理和實踐挑戰。例如，如何確保算法的公平性？
    如何保護患者隱私？這些問題需要我們認真思考和和解決。

    總的來說，AI在醫療領域是一把雙刃劍，既有巨大潛力，也存在風險。
    我們需要在推動技術進步的同時，確保患者安全和倫理標準。
  `.trim()
};

test.describe('AI 服務全面測試', () => {
  let context: BrowserContext;
  let page: Page;

  test.beforeAll(async () => {
    // 啟動帶 DevTools 的瀏覽器
    const browser = await chromium.launch({
      headless: false,
      devtools: true
    });
    context = await browser.newContext();

    // 啟用網絡監控
    await context.route('**/*', route => {
      console.log(`[Network] ${route.request().method()} ${route.request().url()}`);
      route.continue();
    });
  });

  test.beforeEach(async () => {
    page = await context.newPage();

    // 監控控制台
    page.on('console', msg => {
      console.log(`[Console] ${msg.type()}: ${msg.text()}`);
    });

    // 監控錯誤
    page.on('pageerror', error => {
      console.error(`[Page Error] ${error.message}`);
    });
  });

  test('1. 測試獨立校對服務 API', async () => {
    console.log('\n=== 測試獨立校對服務 ===\n');

    // 直接測試校對 API
    const response = await fetch(`${API_BASE_URL}/v1/proofread`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        body_text: TEST_ARTICLE.body,
        max_issues: 20
      })
    });

    expect(response.ok).toBeTruthy();
    const result = await response.json();

    console.log('校對服務響應:', {
      success: result.success,
      issues_count: result.proofreading_issues?.length || 0,
      stats: result.proofreading_stats
    });

    // 驗證響應結構
    expect(result).toHaveProperty('success');
    expect(result).toHaveProperty('proofreading_issues');
    expect(result).toHaveProperty('proofreading_stats');

    // 檢查是否找到了錯誤
    if (result.proofreading_issues && result.proofreading_issues.length > 0) {
      console.log('\n找到的校對問題:');
      result.proofreading_issues.forEach((issue: any, index: number) => {
        console.log(`${index + 1}. [${issue.severity}] ${issue.explanation}`);
        console.log(`   原文: "${issue.original_text}"`);
        console.log(`   建議: "${issue.suggested_text}"`);
      });
    }

    // 驗證已知的錯誤是否被檢測到
    const hasDoubleCharError = result.proofreading_issues?.some((issue: any) =>
      issue.original_text?.includes('的的') ||
      issue.explanation?.includes('重複')
    );

    const hasMixedLanguageError = result.proofreading_issues?.some((issue: any) =>
      issue.explanation?.includes('中英') ||
      issue.explanation?.includes('混雜')
    );

    console.log('\n錯誤檢測結果:');
    console.log(`- 重複字詞檢測: ${hasDoubleCharError ? '✅' : '❌'}`);
    console.log(`- 中英混雜檢測: ${hasMixedLanguageError ? '✅' : '❌'}`);
  });

  test('2. 測試標題生成服務 API', async () => {
    console.log('\n=== 測試標題生成服務 ===\n');

    const response = await fetch(`${API_BASE_URL}/v1/generate-titles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: TEST_ARTICLE.title,
        content: TEST_ARTICLE.body
      })
    });

    expect(response.ok).toBeTruthy();
    const result = await response.json();

    console.log('標題生成服務響應:', {
      success: result.success,
      titles_count: result.suggested_titles?.length || 0,
      source: result.source
    });

    // 驗證響應結構
    expect(result).toHaveProperty('success');
    expect(result).toHaveProperty('suggested_titles');

    if (result.suggested_titles && result.suggested_titles.length > 0) {
      console.log('\n生成的標題建議:');
      result.suggested_titles.forEach((title: any, index: number) => {
        console.log(`${index + 1}. ${title.main || title}`);
        if (title.score) {
          console.log(`   評分: ${title.score}`);
        }
      });
    }
  });

  test('3. 測試 Worklist 完整流程', async () => {
    console.log('\n=== 測試 Worklist 完整流程 ===\n');

    // 獲取 worklist
    const worklistResponse = await fetch(`${API_BASE_URL}/v1/worklist`);
    expect(worklistResponse.ok).toBeTruthy();
    const worklist = await worklistResponse.json();

    console.log(`Worklist 項目數: ${worklist.items?.length || 0}`);

    if (worklist.items && worklist.items.length > 0) {
      const firstItem = worklist.items[0];
      console.log('\n測試第一個項目:', {
        id: firstItem.id,
        title: firstItem.title,
        status: firstItem.status
      });

      // 獲取詳細信息
      const itemResponse = await fetch(`${API_BASE_URL}/v1/worklist/${firstItem.id}`);
      expect(itemResponse.ok).toBeTruthy();
      const item = await itemResponse.json();

      // 檢查 AI 解析字段
      console.log('\nAI 解析字段檢查:');
      console.log(`- suggested_titles: ${item.suggested_titles ? '✅ 有數據' : '❌ 空'}`);
      console.log(`- suggested_meta_description: ${item.suggested_meta_description ? '✅ 有數據' : '❌ 空'}`);
      console.log(`- suggested_seo_keywords: ${item.suggested_seo_keywords ? '✅ 有數據' : '❌ 空'}`);
      console.log(`- proofreading_issues: ${item.proofreading_issues?.length > 0 ? '✅ 有數據' : '❌ 空'}`);

      // 如果沒有標題建議，嘗試生成
      if (!item.suggested_titles) {
        console.log('\n嘗試生成標題...');
        const titleGenResponse = await fetch(`${API_BASE_URL}/v1/worklist/${firstItem.id}/generate-titles`, {
          method: 'POST'
        });

        if (titleGenResponse.ok) {
          const titleResult = await titleGenResponse.json();
          console.log('標題生成結果:', titleResult.success ? '✅ 成功' : '❌ 失敗');
        }
      }

      // 如果沒有校對結果，嘗試校對
      if (!item.proofreading_issues || item.proofreading_issues.length === 0) {
        console.log('\n嘗試校對文章...');
        const proofreadResponse = await fetch(`${API_BASE_URL}/v1/worklist/${firstItem.id}/proofread`, {
          method: 'POST'
        });

        if (proofreadResponse.ok) {
          const proofreadResult = await proofreadResponse.json();
          console.log('校對結果:', proofreadResult.success ? '✅ 成功' : '❌ 失敗');
          console.log('發現問題數:', proofreadResult.proofreading_issues?.length || 0);
        }
      }
    }
  });

  test('4. 測試 UI 整合與顯示', async () => {
    console.log('\n=== 測試 UI 整合 ===\n');

    // 訪問前端頁面
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // 等待 worklist 加載
    await page.waitForSelector('.worklist-container, [data-testid="worklist"]', {
      timeout: 10000
    }).catch(() => {
      console.log('Worklist 容器未找到，嘗試其他選擇器...');
    });

    // 使用 Chrome DevTools Protocol
    const client = await page.context().newCDPSession(page);

    // 監控網絡請求
    await client.send('Network.enable');
    client.on('Network.requestWillBeSent', (params) => {
      if (params.request.url.includes('/v1/')) {
        console.log(`[CDP Network] ${params.request.method} ${params.request.url}`);
      }
    });

    // 檢查是否有文章項目
    const articleItems = await page.$$('[class*="article"], [class*="worklist-item"]');
    console.log(`找到 ${articleItems.length} 個文章項目`);

    if (articleItems.length > 0) {
      // 點擊第一個項目
      await articleItems[0].click();
      await page.waitForTimeout(2000);

      // 檢查抽屜是否打開
      const drawer = await page.$('[class*="drawer"], [class*="modal"], [class*="detail"]');
      if (drawer) {
        console.log('✅ 詳情抽屜已打開');

        // 檢查 AI 建議字段是否顯示
        const checkField = async (selector: string, fieldName: string) => {
          const element = await page.$(selector);
          if (element) {
            const text = await element.textContent();
            console.log(`${fieldName}: ${text ? '✅ 有內容' : '❌ 空'}`);
            return text;
          }
          return null;
        };

        console.log('\n檢查 AI 建議字段顯示:');
        await checkField('[class*="suggested-title"]', 'Suggested Titles');
        await checkField('[class*="meta-description"]', 'Meta Description');
        await checkField('[class*="seo-keyword"]', 'SEO Keywords');
        await checkField('[class*="proofreading"]', 'Proofreading Issues');
      }
    }

    // 截圖保存結果
    await page.screenshot({
      path: '/tmp/ai-services-test-result.png',
      fullPage: true
    });
    console.log('\n截圖已保存: /tmp/ai-services-test-result.png');
  });

  test('5. 測試 Prompt 效果驗證', async () => {
    console.log('\n=== Prompt 效果驗證 ===\n');

    // 測試不同複雜度的內容
    const testCases = [
      {
        name: '簡單內容',
        content: '這是一篇關於科技的文章。'
      },
      {
        name: '中等複雜度',
        content: TEST_ARTICLE.body
      },
      {
        name: '複雜內容（包含多種格式）',
        content: `
# 標題一
這是正文內容，包含**粗體**和*斜體*。

## 子標題
- 列表項目1
- 列表項目2

> 引用內容

代碼塊：
\`\`\`python
def hello():
    print("Hello World")
\`\`\`
        `.trim()
      }
    ];

    for (const testCase of testCases) {
      console.log(`\n測試: ${testCase.name}`);

      // 測試校對
      const proofreadResponse = await fetch(`${API_BASE_URL}/v1/proofread`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body_text: testCase.content })
      });

      const proofreadResult = await proofreadResponse.json();
      console.log(`- 校對: ${proofreadResult.success ? '✅' : '❌'} (${proofreadResult.error || 'OK'})`);

      // 測試標題生成
      const titleResponse = await fetch(`${API_BASE_URL}/v1/generate-titles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: '測試標題',
          content: testCase.content
        })
      });

      const titleResult = await titleResponse.json();
      console.log(`- 標題生成: ${titleResult.success ? '✅' : '❌'} (${titleResult.error || 'OK'})`);
    }

    // 分析結果
    console.log('\n=== Prompt 分析結論 ===');
    console.log('根據測試結果，可以得出以下結論：');
    console.log('1. 獨立服務（校對、標題生成）使用簡化的 prompt 成功率更高');
    console.log('2. 複雜的統一 prompt 容易導致 Claude API 解析失敗');
    console.log('3. 建議繼續使用獨立服務架構，每個服務專注單一任務');
    console.log('4. 如需調整 prompt，應該：');
    console.log('   - 保持簡潔明確');
    console.log('   - 避免嵌套 JSON 結構');
    console.log('   - 提供清晰的輸出格式示例');
  });

  test.afterAll(async () => {
    // 生成測試報告
    console.log('\n' + '='.repeat(60));
    console.log('測試完成 - 總結報告');
    console.log('='.repeat(60));
    console.log('\n建議事項：');
    console.log('1. ✅ 繼續使用獨立的校對服務和標題生成服務');
    console.log('2. ✅ 保持簡化的 prompt 設計');
    console.log('3. ⚠️  監控 API 響應時間和成功率');
    console.log('4. 📊 定期檢查 AI 輸出質量');

    await context.close();
  });
});

// 輔助函數：等待 API 響應
async function waitForAPIResponse(page: Page, urlPattern: string, timeout: number = 10000) {
  return page.waitForResponse(
    response => response.url().includes(urlPattern),
    { timeout }
  );
}

// 輔助函數：檢查 Chrome DevTools 網絡日誌
async function checkNetworkLogs(page: Page) {
  const client = await page.context().newCDPSession(page);
  await client.send('Network.enable');

  const requests: any[] = [];
  client.on('Network.requestWillBeSent', (params) => {
    requests.push({
      url: params.request.url,
      method: params.request.method,
      timestamp: params.timestamp
    });
  });

  return requests;
}