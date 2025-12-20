/**
 * 验证原文和建议字段是否显示内容
 */

const { chromium } = require('playwright');

const BASE_URL = 'https://storage.googleapis.com/cms-automation-frontend-2025/index.html';
const TEST_EMAIL = 'allen.chen@epochtimes.com';
const TEST_PASSWORD = 'Editor123$';

async function runTest() {
  console.log('\n========================================');
  console.log('  验证原文/建议字段修复');
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  try {
    // 1. 登录
    console.log('1. 登录中...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    await page.fill('input[type="email"]', TEST_EMAIL);
    await page.fill('input[type="password"]', TEST_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    // 2. 导航到校对审核页面
    const correctUrl = `${BASE_URL}#/worklist/13/review`;
    console.log('2. 导航到校对审核页面:', correctUrl);
    await page.goto(correctUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(8000);

    // 3. 等待页面完全加载
    console.log('3. 等待页面加载...');
    await page.waitForSelector('text=Issue Details', { timeout: 15000 }).catch(() => null);
    await page.waitForTimeout(2000);

    // 4. 检查Issue Details面板中的原文和建议
    console.log('4. 检查Issue Details面板...');

    const issueDetails = await page.evaluate(() => {
      const body = document.body.innerText;

      // 查找 Original 和 Suggested 标签后的内容
      const originalMatch = body.match(/Original\s*\n([^\n]+)/);
      const suggestedMatch = body.match(/Suggested\s*\n([^\n]+)/);

      // 也检查中文标签
      const originalZhMatch = body.match(/原文[：:]\s*([^\n]+)/);
      const suggestedZhMatch = body.match(/建议[：:]\s*([^\n]+)/);

      // 查找所有包含 bg-red 或 bg-green 的元素 (原文/建议的背景色)
      const redBgElements = document.querySelectorAll('[class*="bg-red"]');
      const greenBgElements = document.querySelectorAll('[class*="bg-green"]');

      const redBgTexts = Array.from(redBgElements)
        .map(el => el.textContent?.trim())
        .filter(t => t && t.length > 0);

      const greenBgTexts = Array.from(greenBgElements)
        .map(el => el.textContent?.trim())
        .filter(t => t && t.length > 0);

      // 查找 Issue Detail 面板内容
      const detailPanel = document.querySelector('[class*="issue-detail"], [class*="IssueDetail"]');
      const detailPanelText = detailPanel?.textContent || '';

      // 检查是否有空的原文/建议模式 (问题的症状)
      const hasEmptyPattern = body.includes('原文: \n建议') ||
                             body.includes('Original: \nSuggested') ||
                             body.includes('原文:\n建议');

      return {
        originalMatch: originalMatch ? originalMatch[1] : null,
        suggestedMatch: suggestedMatch ? suggestedMatch[1] : null,
        originalZhMatch: originalZhMatch ? originalZhMatch[1] : null,
        suggestedZhMatch: suggestedZhMatch ? suggestedZhMatch[1] : null,
        redBgTexts: redBgTexts.slice(0, 5),
        greenBgTexts: greenBgTexts.slice(0, 5),
        hasEmptyPattern,
        bodySnippet: body.substring(0, 3000)
      };
    });

    console.log('\n=== 检测结果 ===');
    console.log('Original 标签后内容:', issueDetails.originalMatch || '(未找到)');
    console.log('Suggested 标签后内容:', issueDetails.suggestedMatch || '(未找到)');
    console.log('原文 标签后内容:', issueDetails.originalZhMatch || '(未找到)');
    console.log('建议 标签后内容:', issueDetails.suggestedZhMatch || '(未找到)');
    console.log('红色背景文本 (原文):', issueDetails.redBgTexts.length > 0 ? issueDetails.redBgTexts : '(无)');
    console.log('绿色背景文本 (建议):', issueDetails.greenBgTexts.length > 0 ? issueDetails.greenBgTexts : '(无)');
    console.log('存在空白模式:', issueDetails.hasEmptyPattern ? '是 (问题仍存在!)' : '否 (问题已修复)');

    // 5. 截图Issue Details面板
    await page.screenshot({ path: '/tmp/verify_fix_full.png', fullPage: true });

    // 尝试截取右侧面板
    const rightPanel = await page.$('[class*="border-l"]');
    if (rightPanel) {
      await rightPanel.screenshot({ path: '/tmp/verify_fix_detail_panel.png' });
    }

    // 6. 在左侧列表中查找issue内容
    console.log('\n=== 左侧Issue列表内容 ===');
    const issueListContent = await page.evaluate(() => {
      // 查找issue列表项
      const issueItems = document.querySelectorAll('[class*="issue"], [class*="cursor-pointer"]');
      const items = [];

      issueItems.forEach(item => {
        const text = item.textContent || '';
        // 查找包含 → 的项 (表示 原文 → 建议 格式)
        if (text.includes('→') && text.length > 20 && text.length < 500) {
          items.push(text.replace(/\s+/g, ' ').substring(0, 150));
        }
      });

      return items.slice(0, 5);
    });

    if (issueListContent.length > 0) {
      console.log('找到的Issue项:');
      issueListContent.forEach((item, i) => {
        console.log(`  [${i+1}] ${item}`);
      });
    }

    // 7. 最终判定
    console.log('\n========================================');

    const hasOriginalContent = issueDetails.originalMatch || issueDetails.originalZhMatch || issueDetails.redBgTexts.length > 0;
    const hasSuggestedContent = issueDetails.suggestedMatch || issueDetails.suggestedZhMatch || issueDetails.greenBgTexts.length > 0;
    const issueListHasContent = issueListContent.length > 0;

    if (hasOriginalContent && hasSuggestedContent && !issueDetails.hasEmptyPattern) {
      console.log('  ✅ 验证通过: 原文和建议字段显示正常!');
      console.log('========================================\n');
      return true;
    } else if (issueListHasContent && !issueDetails.hasEmptyPattern) {
      console.log('  ✅ 验证通过: Issue列表显示了原文→建议内容');
      console.log('========================================\n');
      return true;
    } else if (issueDetails.hasEmptyPattern) {
      console.log('  ❌ 验证失败: 检测到空白的原文/建议模式');
      console.log('========================================\n');
      return false;
    } else {
      console.log('  ⚠️  验证不确定: 请手动检查截图');
      console.log('  截图位置: /tmp/verify_fix_full.png');
      console.log('========================================\n');
      return false;
    }

  } catch (error) {
    console.log('错误:', error.message);
    await page.screenshot({ path: '/tmp/verify_fix_error.png' });
    return false;
  } finally {
    await browser.close();
  }
}

runTest().then(success => {
  console.log(success ? '测试通过!' : '测试失败或需要手动验证');
  process.exit(success ? 0 : 1);
});
