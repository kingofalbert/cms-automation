/**
 * 模拟用户操作流程
 */

const { chromium } = require('playwright');

const BASE_URL = 'https://storage.googleapis.com/cms-automation-frontend-2025/index.html';
const TEST_EMAIL = 'allen.chen@epochtimes.com';
const TEST_PASSWORD = 'Editor123$';

async function runTest() {
  console.log('\n========================================');
  console.log('  模拟用户操作流程');
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // 捕获控制台消息
  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push({ type: msg.type(), text: msg.text() });
  });

  // 捕获网络请求
  const networkRequests = [];
  page.on('request', request => {
    if (request.url().includes('api') || request.url().includes('worklist')) {
      networkRequests.push({ url: request.url(), method: request.method() });
    }
  });

  page.on('requestfailed', request => {
    console.log('请求失败:', request.url(), request.failure()?.errorText);
  });

  try {
    // 1. 登录
    console.log('1. 登录...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    await page.fill('input[type="email"]', TEST_EMAIL);
    await page.fill('input[type="password"]', TEST_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    console.log('   URL:', page.url());
    await page.screenshot({ path: '/tmp/flow_1_worklist.png' });

    // 2. 检查 worklist 项目
    console.log('\n2. 检查 worklist 项目...');
    const worklistItems = await page.evaluate(() => {
      const rows = document.querySelectorAll('table tbody tr');
      return Array.from(rows).map((row, index) => {
        const cells = row.querySelectorAll('td');
        const statusBadge = row.querySelector('[class*="badge"], [class*="Badge"]');
        return {
          index,
          title: cells[0]?.textContent?.trim()?.substring(0, 50),
          status: statusBadge?.textContent?.trim() || cells[1]?.textContent?.trim(),
          hasClickHandler: row.onclick !== null || row.style.cursor === 'pointer'
        };
      });
    });

    console.log('   Worklist 项目:');
    worklistItems.forEach((item, i) => {
      console.log(`   [${i}] ${item.title} - ${item.status}`);
    });

    // 3. 点击第一个项目
    console.log('\n3. 点击第一个项目...');
    const firstRow = await page.$('table tbody tr:first-child');
    if (firstRow) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      console.log('   点击后 URL:', page.url());
      await page.screenshot({ path: '/tmp/flow_2_after_click.png' });
    }

    // 4. 检查是否有 Review 按钮
    console.log('\n4. 检查 Review 按钮...');
    const reviewBtn = await page.$('button:has-text("Review"), a:has-text("Review"), button:has-text("校对审核")');
    if (reviewBtn) {
      console.log('   找到 Review 按钮，点击...');
      await reviewBtn.click();
      await page.waitForTimeout(5000);
      console.log('   点击后 URL:', page.url());
    } else {
      console.log('   未找到 Review 按钮');

      // 检查是否有其他导航选项
      const allButtons = await page.$$eval('button', btns => btns.map(b => b.textContent?.trim()).filter(t => t));
      console.log('   页面上的按钮:', allButtons.slice(0, 10));
    }

    await page.screenshot({ path: '/tmp/flow_3_review_page.png' });

    // 5. 检查当前页面状态
    console.log('\n5. 检查页面状态...');
    const pageState = await page.evaluate(() => {
      const body = document.body.innerText;
      const url = window.location.href;
      const hash = window.location.hash;

      // 检查是否在 Loading 状态
      const isLoading = body.includes('Loading') || document.querySelector('.animate-spin') !== null;

      // 检查是否有错误
      const hasError = body.includes('Error') || body.includes('error') || body.includes('失败');

      // 检查原文和建议
      const hasOriginal = body.includes('Original') || body.includes('原文');
      const hasSuggested = body.includes('Suggested') || body.includes('建议');

      return {
        url,
        hash,
        bodyLength: body.length,
        isLoading,
        hasError,
        hasOriginal,
        hasSuggested,
        bodyPreview: body.substring(0, 1000)
      };
    });

    console.log('   URL:', pageState.url);
    console.log('   Hash:', pageState.hash);
    console.log('   Body 长度:', pageState.bodyLength);
    console.log('   Loading 状态:', pageState.isLoading);
    console.log('   有错误:', pageState.hasError);
    console.log('   有 Original:', pageState.hasOriginal);
    console.log('   有 Suggested:', pageState.hasSuggested);

    // 6. 如果在 Loading 状态，等待更长时间
    if (pageState.isLoading) {
      console.log('\n6. 页面在 Loading，等待更长时间...');
      await page.waitForTimeout(15000);
      await page.screenshot({ path: '/tmp/flow_4_after_wait.png' });

      const finalState = await page.evaluate(() => {
        const body = document.body.innerText;
        return {
          isLoading: body.includes('Loading') || document.querySelector('.animate-spin') !== null,
          bodyPreview: body.substring(0, 500)
        };
      });

      console.log('   仍在 Loading:', finalState.isLoading);
      console.log('   内容:', finalState.bodyPreview);
    }

    // 7. 检查控制台错误
    console.log('\n7. 控制台错误:');
    const errors = consoleMessages.filter(m => m.type === 'error');
    if (errors.length > 0) {
      errors.slice(0, 10).forEach(e => console.log('   -', e.text.substring(0, 200)));
    } else {
      console.log('   无错误');
    }

    // 8. 检查网络请求
    console.log('\n8. API 请求:');
    networkRequests.slice(0, 10).forEach(r => console.log('   -', r.method, r.url.substring(0, 100)));

    console.log('\n========================================');
    console.log('截图保存到 /tmp/flow_*.png');
    console.log('========================================\n');

  } catch (error) {
    console.log('错误:', error.message);
    await page.screenshot({ path: '/tmp/flow_error.png' });
  } finally {
    await browser.close();
  }
}

runTest();
