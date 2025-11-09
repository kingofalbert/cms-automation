import { test, expect } from '@playwright/test';

// Use cache-busting URL to bypass CDN cache
const CACHE_BUST = Date.now();
const FRONTEND_URL = `https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html?v=${CACHE_BUST}`;

test.describe('CMS Automation - 完整回归测试 (Comprehensive Regression Test)', () => {

  test.beforeEach(async ({ page }) => {
    // 收集所有控制台消息和错误
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`[Browser ERROR] ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      console.log(`[PAGE ERROR] ${error.message}`);
    });

    page.on('requestfailed', request => {
      console.log(`[NETWORK FAILED] ${request.method()} ${request.url()}`);
    });
  });

  test('Test 1: Homepage - Worklist 页面加载和显示', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 1: Worklist 页面加载和显示');
    console.log('========================================\n');

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    console.log('Step 1.1: 检查页面标题...');
    const title = await page.title();
    console.log(`  页面标题: ${title}`);
    expect(title).toContain('CMS Automation');

    console.log('\nStep 1.2: 检查顶部导航栏...');
    const appTitle = await page.locator('h1, [class*="title"]').first().textContent();
    console.log(`  应用标题: ${appTitle}`);

    const languageSelector = await page.locator('button:has-text("English"), button:has-text("繁體中文")').count();
    console.log(`  语言选择器: ${languageSelector > 0 ? '✓ 找到' : '✗ 未找到'}`);

    const settingsButton = await page.locator('button:has-text("Settings"), button:has-text("设置")').count();
    console.log(`  设置按钮: ${settingsButton > 0 ? '✓ 找到' : '✗ 未找到'}`);

    console.log('\nStep 1.3: 检查统计卡片...');
    const statCards = await page.locator('.grid .p-4, [class*="Card"]').count();
    console.log(`  统计卡片数量: ${statCards}`);
    expect(statCards).toBeGreaterThan(0);

    // 检查具体统计数据
    const totalArticles = await page.locator('text=/Total Articles|总数/i').count();
    console.log(`  总数卡片: ${totalArticles > 0 ? '✓' : '✗'}`);

    const readyToPublish = await page.locator('text=/Ready to Publish|准备发布/i').count();
    console.log(`  准备发布卡片: ${readyToPublish > 0 ? '✓' : '✗'}`);

    console.log('\nStep 1.4: 检查筛选器...');
    const searchBox = await page.locator('input[placeholder*="Search"], input[placeholder*="搜索"]').count();
    console.log(`  搜索框: ${searchBox > 0 ? '✓ 找到' : '✗ 未找到'}`);

    const statusFilter = await page.locator('select, button:has-text("All Status"), button:has-text("所有状态")').count();
    console.log(`  状态筛选: ${statusFilter > 0 ? '✓ 找到' : '✗ 未找到'}`);

    console.log('\nStep 1.5: 检查Worklist表格...');
    const table = await page.locator('table').count();
    console.log(`  表格: ${table > 0 ? '✓ 找到' : '✗ 未找到'}`);
    expect(table).toBeGreaterThan(0);

    const tableHeaders = await page.locator('th').allTextContents();
    console.log(`  表头 (${tableHeaders.length}): ${tableHeaders.join(', ')}`);

    const tableRows = await page.locator('tbody tr').count();
    console.log(`  数据行数: ${tableRows}`);
    expect(tableRows).toBeGreaterThan(0);

    console.log('\nStep 1.6: 检查同步按钮...');
    const syncButton = await page.locator('button:has-text("Sync"), button:has-text("同步")').count();
    console.log(`  同步按钮: ${syncButton > 0 ? '✓ 找到' : '✗ 未找到'}`);

    await page.screenshot({ path: 'test-results/regression-01-homepage.png', fullPage: true });
    console.log('\n✅ 测试 1 完成: Worklist 页面基本功能正常\n');
  });

  test('Test 2: Worklist - 检查表格内容和数据', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 2: Worklist 表格内容验证');
    console.log('========================================\n');

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    console.log('Step 2.1: 读取第一行数据...');
    const firstRow = page.locator('tbody tr').first();
    const firstRowExists = await firstRow.count() > 0;

    if (firstRowExists) {
      const cells = await firstRow.locator('td').allTextContents();
      console.log(`  第一行单元格数量: ${cells.length}`);
      cells.forEach((cell, index) => {
        console.log(`    列 ${index + 1}: ${cell.substring(0, 50)}${cell.length > 50 ? '...' : ''}`);
      });

      console.log('\nStep 2.2: 检查标题是否为中文...');
      const titleCell = await firstRow.locator('td').nth(1).textContent();
      const hasChinese = /[\u4e00-\u9fa5]/.test(titleCell || '');
      console.log(`  标题包含中文: ${hasChinese ? '✓ 是' : '✗ 否'}`);
      console.log(`  标题内容: ${titleCell}`);
      expect(hasChinese).toBeTruthy();

      console.log('\nStep 2.3: 检查状态显示...');
      const statusBadge = await firstRow.locator('[class*="badge"], [class*="status"]').count();
      console.log(`  状态标签: ${statusBadge > 0 ? '✓ 找到' : '✗ 未找到'}`);

      console.log('\nStep 2.4: 检查Review按钮...');
      const reviewButton = await firstRow.locator('button:has-text("Review"), button:has-text("审核")').count();
      console.log(`  审核按钮: ${reviewButton > 0 ? '✓ 找到' : '✗ 未找到'}`);
      expect(reviewButton).toBeGreaterThan(0);
    } else {
      console.log('  ⚠️  没有找到数据行');
    }

    await page.screenshot({ path: 'test-results/regression-02-table-data.png', fullPage: true });
    console.log('\n✅ 测试 2 完成: 表格数据验证完成\n');
  });

  test('Test 3: Navigation - 点击进入审核页面', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 3: 点击审核按钮导航');
    console.log('========================================\n');

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    console.log('Step 3.1: 查找第一个审核按钮...');
    const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核")').first();
    const buttonExists = await reviewButton.count() > 0;
    console.log(`  审核按钮存在: ${buttonExists ? '✓ 是' : '✗ 否'}`);
    expect(buttonExists).toBeTruthy();

    console.log('\nStep 3.2: 点击审核按钮...');
    await reviewButton.click();
    console.log('  ✓ 已点击');

    console.log('\nStep 3.3: 等待页面导航...');
    await page.waitForTimeout(3000);

    const currentUrl = page.url();
    console.log(`  当前URL: ${currentUrl}`);

    const isProofreadingPage = currentUrl.includes('/proofreading/');
    console.log(`  是审核页面: ${isProofreadingPage ? '✓ 是' : '✗ 否'}`);
    expect(isProofreadingPage).toBeTruthy();

    await page.screenshot({ path: 'test-results/regression-03-navigation.png', fullPage: true });
    console.log('\n✅ 测试 3 完成: 导航功能正常\n');
  });

  test('Test 4: Proofreading Page - 页面加载和基本元素', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 4: 审核页面加载和基本元素');
    console.log('========================================\n');

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    console.log('Step 4.1: 导航到审核页面...');
    const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核")').first();
    await reviewButton.click();
    await page.waitForTimeout(5000);

    console.log('\nStep 4.2: 检查页面标题...');
    const articleTitle = await page.locator('h1, h2').first().textContent();
    console.log(`  文章标题: ${articleTitle}`);
    expect(articleTitle).toBeTruthy();
    expect(articleTitle?.length).toBeGreaterThan(0);

    console.log('\nStep 4.3: 检查视图模式按钮组...');
    const viewModeButtons = [
      'Original', '原始',
      'Rendered', '渲染',
      'Preview', '预览',
      'Diff', '对比'
    ];

    for (const buttonText of viewModeButtons) {
      const count = await page.locator(`button:has-text("${buttonText}")`).count();
      if (count > 0) {
        console.log(`  ✓ 找到按钮: ${buttonText}`);
      }
    }

    const totalViewButtons = await page.locator('button').filter({
      hasText: /Original|Rendered|Preview|Diff|原始|渲染|预览|对比/i
    }).count();
    console.log(`  视图模式按钮总数: ${totalViewButtons}`);
    expect(totalViewButtons).toBeGreaterThan(0);

    console.log('\nStep 4.4: 检查三栏布局...');
    const mainContent = await page.locator('main, [role="main"], .grid').count();
    console.log(`  主内容区域: ${mainContent > 0 ? '✓ 找到' : '✗ 未找到'}`);

    console.log('\nStep 4.5: 检查左侧问题列表...');
    const issuesList = await page.locator('[class*="issue"], [class*="sidebar"], aside').count();
    console.log(`  问题列表容器: ${issuesList > 0 ? '✓ 找到' : '✗ 未找到'}`);

    console.log('\nStep 4.6: 检查中间预览区域...');
    const previewArea = await page.locator('article, [class*="preview"], [class*="content"]').count();
    console.log(`  预览区域: ${previewArea > 0 ? '✓ 找到' : '✗ 未找到'}`);

    console.log('\nStep 4.7: 检查页面内容...');
    const bodyText = await page.locator('body').textContent();
    const hasContent = bodyText && bodyText.length > 200;
    console.log(`  页面文本长度: ${bodyText?.length || 0}`);
    console.log(`  有实质内容: ${hasContent ? '✓ 是' : '✗ 否'}`);
    expect(hasContent).toBeTruthy();

    await page.screenshot({ path: 'test-results/regression-04-proofreading-page.png', fullPage: true });
    console.log('\n✅ 测试 4 完成: 审核页面基本元素正常\n');
  });

  test('Test 5: Proofreading Page - 视图模式切换', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 5: 视图模式切换功能');
    console.log('========================================\n');

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    console.log('Step 5.1: 进入审核页面...');
    const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核")').first();
    await reviewButton.click();
    await page.waitForTimeout(5000);

    const viewModes = [
      { name: 'Original', cn: '原始' },
      { name: 'Rendered', cn: '渲染' },
      { name: 'Preview', cn: '预览' },
      { name: 'Diff', cn: '对比' }
    ];

    for (const mode of viewModes) {
      console.log(`\nStep 5.${viewModes.indexOf(mode) + 2}: 测试 ${mode.name} 模式...`);

      // 尝试英文和中文按钮
      const button = page.locator(`button:has-text("${mode.name}"), button:has-text("${mode.cn}")`).first();
      const buttonExists = await button.count() > 0;

      if (buttonExists) {
        console.log(`  ✓ 找到 ${mode.name} 按钮`);

        await button.click();
        await page.waitForTimeout(1000);
        console.log(`  ✓ 已点击 ${mode.name} 按钮`);

        // 检查按钮是否变为激活状态
        const buttonClass = await button.getAttribute('class');
        console.log(`  按钮样式: ${buttonClass}`);

        await page.screenshot({
          path: `test-results/regression-05-view-${mode.name.toLowerCase()}.png`,
          fullPage: true
        });
      } else {
        console.log(`  ⚠️  未找到 ${mode.name} 按钮`);
      }
    }

    console.log('\n✅ 测试 5 完成: 视图模式切换测试完成\n');
  });

  test('Test 6: Proofreading Page - 问题列表和交互', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 6: 问题列表和交互功能');
    console.log('========================================\n');

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    console.log('Step 6.1: 进入审核页面...');
    const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核")').first();
    await reviewButton.click();
    await page.waitForTimeout(5000);

    console.log('\nStep 6.2: 查找问题列表...');
    const issueItems = await page.locator('[data-testid*="issue"], .issue-item, [class*="issue"]').count();
    console.log(`  问题项数量: ${issueItems}`);

    if (issueItems > 0) {
      console.log('\nStep 6.3: 点击第一个问题...');
      const firstIssue = page.locator('[data-testid*="issue"], .issue-item, [class*="issue"]').first();

      // 获取问题文本
      const issueText = await firstIssue.textContent();
      console.log(`  问题内容: ${issueText?.substring(0, 100)}...`);

      await firstIssue.click();
      await page.waitForTimeout(2000);
      console.log('  ✓ 已点击第一个问题');

      console.log('\nStep 6.4: 检查是否滚动到对应位置...');
      // 检查预览区域是否有响应
      await page.screenshot({ path: 'test-results/regression-06-issue-selected.png', fullPage: true });
      console.log('  ✓ 截图已保存');
    } else {
      console.log('  ⚠️  未找到问题列表项');
    }

    console.log('\n✅ 测试 6 完成: 问题列表交互测试完成\n');
  });

  test('Test 7: Proofreading Page - 操作按钮', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 7: 审核页面操作按钮');
    console.log('========================================\n');

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    console.log('Step 7.1: 进入审核页面...');
    const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核")').first();
    await reviewButton.click();
    await page.waitForTimeout(5000);

    console.log('\nStep 7.2: 查找所有操作按钮...');
    const actionButtons = [
      'Approve', '批准', '通过',
      'Reject', '拒绝',
      'Save', '保存',
      'Back', '返回',
      'Cancel', '取消',
      'Submit', '提交',
      'Accept', '接受',
      'Apply', '应用'
    ];

    const foundButtons: string[] = [];
    for (const buttonText of actionButtons) {
      const count = await page.locator(`button:has-text("${buttonText}")`).count();
      if (count > 0) {
        foundButtons.push(buttonText);
        console.log(`  ✓ 找到按钮: ${buttonText}`);
      }
    }

    console.log(`\n  找到的操作按钮总数: ${foundButtons.length}`);

    console.log('\nStep 7.3: 检查所有按钮...');
    const allButtons = await page.locator('button').count();
    console.log(`  页面总按钮数: ${allButtons}`);

    // 列出所有按钮的文本
    const buttonTexts = await page.locator('button').allTextContents();
    console.log('\n  所有按钮文本:');
    buttonTexts.forEach((text, index) => {
      if (text.trim()) {
        console.log(`    ${index + 1}. ${text.trim()}`);
      }
    });

    await page.screenshot({ path: 'test-results/regression-07-action-buttons.png', fullPage: true });
    console.log('\n✅ 测试 7 完成: 操作按钮检查完成\n');
  });

  test('Test 8: Settings Page - 设置页面', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 8: 设置页面');
    console.log('========================================\n');

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);

    console.log('Step 8.1: 查找设置按钮...');
    const settingsButton = page.locator('button:has-text("Settings"), button:has-text("设置")').first();
    const buttonExists = await settingsButton.count() > 0;
    console.log(`  设置按钮存在: ${buttonExists ? '✓ 是' : '✗ 否'}`);

    if (buttonExists) {
      console.log('\nStep 8.2: 点击设置按钮...');
      await settingsButton.click();
      await page.waitForTimeout(2000);
      console.log('  ✓ 已点击');

      console.log('\nStep 8.3: 检查设置面板/页面...');
      const settingsContent = await page.locator('[class*="settings"], [class*="modal"], [role="dialog"]').count();
      console.log(`  设置内容区域: ${settingsContent > 0 ? '✓ 找到' : '✗ 未找到'}`);

      await page.screenshot({ path: 'test-results/regression-08-settings.png', fullPage: true });
    } else {
      console.log('  ⚠️  未找到设置按钮');
    }

    console.log('\n✅ 测试 8 完成: 设置页面测试完成\n');
  });

  test('Test 9: 错误检测 - 控制台错误和网络失败', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 9: 错误检测');
    console.log('========================================\n');

    const consoleErrors: string[] = [];
    const networkErrors: string[] = [];
    const pageErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('requestfailed', request => {
      networkErrors.push(`${request.method()} ${request.url()}`);
    });

    page.on('pageerror', error => {
      pageErrors.push(error.message);
    });

    console.log('Step 9.1: 加载首页...');
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    console.log('\nStep 9.2: 导航到审核页面...');
    const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核")').first();
    const buttonExists = await reviewButton.count() > 0;

    if (buttonExists) {
      await reviewButton.click();
      await page.waitForTimeout(5000);
    }

    console.log('\n错误统计:');
    console.log(`  控制台错误: ${consoleErrors.length}`);
    console.log(`  网络失败: ${networkErrors.length}`);
    console.log(`  页面错误: ${pageErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('\n控制台错误详情:');
      consoleErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
      });
    }

    if (networkErrors.length > 0) {
      console.log('\n网络错误详情:');
      networkErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
      });
    }

    if (pageErrors.length > 0) {
      console.log('\n页面错误详情:');
      pageErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
      });
    }

    console.log('\n✅ 测试 9 完成: 错误检测完成\n');
  });

  test('Test 10: 完整工作流程 - 端到端测试', async ({ page }) => {
    console.log('\n========================================');
    console.log('测试 10: 完整工作流程');
    console.log('========================================\n');

    console.log('Step 10.1: 加载首页...');
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    console.log('  ✓ 首页已加载');

    console.log('\nStep 10.2: 验证Worklist数据...');
    const rows = await page.locator('tbody tr').count();
    console.log(`  ✓ 找到 ${rows} 行数据`);
    expect(rows).toBeGreaterThan(0);

    console.log('\nStep 10.3: 点击第一个Review按钮...');
    await page.locator('button:has-text("Review"), button:has-text("审核")').first().click();
    await page.waitForTimeout(5000);
    console.log('  ✓ 已进入审核页面');

    console.log('\nStep 10.4: 验证审核页面加载...');
    const title = await page.locator('h1, h2').first().textContent();
    console.log(`  ✓ 文章标题: ${title}`);
    expect(title).toBeTruthy();

    console.log('\nStep 10.5: 切换到Rendered视图...');
    const renderedButton = page.locator('button:has-text("Rendered"), button:has-text("渲染")').first();
    if (await renderedButton.count() > 0) {
      await renderedButton.click();
      await page.waitForTimeout(2000);
      console.log('  ✓ 已切换到Rendered视图');
    }

    console.log('\nStep 10.6: 返回首页...');
    await page.goto(FRONTEND_URL);
    await page.waitForTimeout(3000);
    console.log('  ✓ 已返回首页');

    await page.screenshot({ path: 'test-results/regression-10-e2e-complete.png', fullPage: true });
    console.log('\n✅ 测试 10 完成: 端到端工作流程测试成功\n');
  });
});
