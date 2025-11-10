# CMS Automation - E2E Regression Test Suite

完整的端到端回归测试套件,使用 Playwright 和 Chrome DevTools 对 CMS 自动化系统进行全面测试。

## 📋 目录

- [测试覆盖范围](#测试覆盖范围)
- [快速开始](#快速开始)
- [测试文件说明](#测试文件说明)
- [运行测试](#运行测试)
- [测试报告](#测试报告)
- [CI/CD 集成](#cicd-集成)
- [最佳实践](#最佳实践)

## 📊 测试覆盖范围

### 功能测试

| 模块 | 测试文件 | 测试数量 | 覆盖率 |
|------|---------|---------|--------|
| Worklist 管理 | `worklist.spec.ts` | 12 | ✅ 完整 |
| 校对审核流程 | `proofreading-review.spec.ts` | 14 | ✅ 完整 |
| 设置页面 | `settings.spec.ts` | 9 | ✅ 完整 |
| Chrome DevTools 集成 | `chrome-devtools-integration.spec.ts` | 7 | ✅ 完整 |
| 完整回归测试 | `complete-regression.spec.ts` | 7 | ✅ 完整 |

**总计**: 49 个测试用例

### 测试类型

- ✅ **功能测试**: 验证所有核心功能
- ✅ **导航测试**: 验证页面间导航
- ✅ **性能测试**: 测量加载时间和性能指标
- ✅ **错误监控**: 检测控制台错误和网络故障
- ✅ **视觉回归**: 自动截图对比
- ✅ **可访问性**: 基本可访问性检查
- ✅ **数据一致性**: 跨页面数据验证

## 🚀 快速开始

### 前置要求

```bash
# Node.js 18+ 和 npm 9+
node --version  # >= 18.0.0
npm --version   # >= 9.0.0
```

### 安装依赖

```bash
cd frontend
npm install
npx playwright install chromium
```

### 运行所有回归测试

```bash
# 针对生产环境运行
npm run test:e2e

# 针对本地开发环境运行
TEST_LOCAL=1 npm run test:e2e

# 运行特定测试文件
npx playwright test e2e/regression/worklist.spec.ts

# 运行并显示浏览器
npx playwright test --headed

# 使用 UI 模式
npx playwright test --ui
```

## 📁 测试文件说明

### 1. `utils/test-helpers.ts`
**工具函数库**

提供可重用的测试工具:
- `navigateWithRetry()`: 带重试的页面导航
- `waitForPageReady()`: 等待页面完全加载
- `createConsoleMonitor()`: 控制台错误监控
- `createNetworkMonitor()`: 网络请求监控
- `measurePerformance()`: 性能指标测量
- `takeScreenshot()`: 截图工具

### 2. `worklist.spec.ts`
**Worklist 管理测试**

测试用例:
- `WL-001`: 页面加载
- `WL-002`: 统计卡片显示
- `WL-003`: 表格数据显示
- `WL-004`: 搜索功能
- `WL-005`: 状态筛选
- `WL-006`: Review 按钮
- `WL-007`: 导航到审核页面
- `WL-008`: 语言选择器
- `WL-009`: 设置按钮
- `WL-010`: 性能指标
- `WL-011`: 控制台错误检查
- `WL-012`: 网络故障检查

### 3. `proofreading-review.spec.ts`
**校对审核流程测试**

测试用例:
- `PR-001`: 审核页面加载
- `PR-002`: 文章标题显示
- `PR-003`: 视图模式按钮
- `PR-004`: 视图模式切换
- `PR-005`: 问题列表显示
- `PR-006`: 问题筛选器
- `PR-007`: 问题详情面板
- `PR-008`: 问题选择
- `PR-009`: 审核备注
- `PR-010`: 操作按钮
- `PR-011`: AI 优化卡片
- `PR-012`: 性能指标
- `PR-013`: Diff 视图性能
- `PR-014`: 交互时错误监控

### 4. `settings.spec.ts`
**设置页面测试**

测试用例:
- `SET-001`: 设置页面加载
- `SET-002`: 设置标题
- `SET-003`: 配置区域
- `SET-004`: 表单输入
- `SET-005`: 保存按钮
- `SET-006`: 返回/取消按钮
- `SET-007`: 导航返回
- `SET-008`: 表单验证
- `SET-009`: 控制台错误检查

### 5. `chrome-devtools-integration.spec.ts`
**Chrome DevTools 集成测试**

高级测试功能:
- `CDT-001`: 网络请求监控
- `CDT-002`: 控制台消息检查
- `CDT-003`: 性能分析
- `CDT-004`: 资源加载分析
- `CDT-005`: 页面快照捕获
- `CDT-006`: 元素结构检查
- `CDT-007`: 内存使用分析

### 6. `complete-regression.spec.ts`
**完整回归测试套件**

端到端工作流:
- `REG-001`: 完整用户流程 (Worklist → Review)
- `REG-002`: 设置页面流程
- `REG-003`: 语言切换
- `REG-004`: 性能基准测试
- `REG-005`: 错误恢复能力测试
- `REG-006`: 可访问性快速检查
- `REG-007`: 跨页面数据一致性

## 🏃 运行测试

### 基本命令

```bash
# 运行所有测试
npm run test:e2e

# 运行特定测试套件
npx playwright test e2e/regression/worklist.spec.ts
npx playwright test e2e/regression/proofreading-review.spec.ts
npx playwright test e2e/regression/settings.spec.ts
npx playwright test e2e/regression/chrome-devtools-integration.spec.ts
npx playwright test e2e/regression/complete-regression.spec.ts

# 运行特定测试用例
npx playwright test -g "WL-001"
npx playwright test -g "Complete user workflow"
```

### 高级选项

```bash
# 显示浏览器窗口
npx playwright test --headed

# 使用 UI 模式 (推荐用于调试)
npx playwright test --ui

# 并行运行 (默认)
npx playwright test --workers=4

# 串行运行
npx playwright test --workers=1

# 只运行失败的测试
npx playwright test --last-failed

# 重试失败的测试
npx playwright test --retries=2

# 调试模式
npx playwright test --debug
```

### 环境配置

```bash
# 测试生产环境 (默认)
npm run test:e2e

# 测试本地开发环境
TEST_LOCAL=1 npm run test:e2e

# 测试本地构建
TEST_LOCAL=1 npm run build && npm run preview
# 在另一个终端:
TEST_LOCAL=1 npm run test:e2e
```

## 📊 测试报告

### 查看 HTML 报告

```bash
# 运行测试后自动生成
npx playwright show-report

# 或者手动打开
open playwright-report/index.html
```

### 报告内容

- ✅ 测试通过/失败统计
- ⏱️ 执行时间
- 📸 失败时截图
- 🎥 测试录像 (失败时)
- 📋 详细日志
- 🔍 网络请求追踪

### 截图和追踪

测试会自动生成:

```
test-results/
├── screenshots/           # 所有测试截图
│   ├── worklist-loaded.png
│   ├── review-page-loaded.png
│   └── ...
├── traces/               # 失败测试的追踪文件
│   └── test-failed-trace.zip
└── videos/              # 失败测试的录像
    └── test-failed-video.webm
```

## 🔄 CI/CD 集成

### GitHub Actions

创建 `.github/workflows/e2e-tests.yml`:

```yaml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        working-directory: ./frontend
        run: |
          npm ci
          npx playwright install --with-deps chromium

      - name: Run E2E tests
        working-directory: ./frontend
        run: npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30

      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-screenshots
          path: frontend/test-results/screenshots/
          retention-days: 30
```

### GitLab CI

创建 `.gitlab-ci.yml`:

```yaml
e2e-tests:
  stage: test
  image: mcr.microsoft.com/playwright:v1.40.0-focal
  script:
    - cd frontend
    - npm ci
    - npm run test:e2e
  artifacts:
    when: always
    paths:
      - frontend/playwright-report/
      - frontend/test-results/
    expire_in: 30 days
```

## 📝 最佳实践

### 1. 编写可靠的测试

```typescript
// ✅ 好: 使用重试机制
await navigateWithRetry(page, url);
await clickWithRetry(button);

// ❌ 差: 直接操作
await page.goto(url);
await button.click();

// ✅ 好: 等待元素可见
await waitForElement(page, 'button:has-text("Submit")');

// ❌ 差: 硬编码等待
await page.waitForTimeout(5000);
```

### 2. 使用描述性测试名称

```typescript
// ✅ 好
test('WL-001: Should load worklist page successfully', async ({ page }) => {
  // ...
});

// ❌ 差
test('test1', async ({ page }) => {
  // ...
});
```

### 3. 测试隔离

```typescript
// ✅ 好: 每个测试独立
test.beforeEach(async ({ page }) => {
  await navigateWithRetry(page, baseURL);
});

// ❌ 差: 测试之间有依赖
```

### 4. 使用监控工具

```typescript
// ✅ 好: 监控错误和性能
const consoleMonitor = createConsoleMonitor(page);
const networkMonitor = createNetworkMonitor(page);
consoleMonitor.start();
networkMonitor.start();

// 执行测试...

consoleMonitor.stop();
networkMonitor.stop();
console.log(consoleMonitor.getReport());
console.log(networkMonitor.getReport());
```

### 5. 截图文档化

```typescript
// ✅ 好: 记录关键步骤
await takeScreenshot(page, 'worklist-loaded');
await takeScreenshot(page, 'review-page-opened');

// 失败时自动截图
if (testInfo.status !== 'passed') {
  await takeScreenshot(page, `${testInfo.title}-failure`);
}
```

## 🐛 调试技巧

### 1. 使用 UI 模式

```bash
npx playwright test --ui
```

最适合:
- 调试失败的测试
- 检查选择器
- 逐步执行测试
- 查看 DOM 快照

### 2. 使用 Debug 模式

```bash
npx playwright test --debug
```

特性:
- 暂停执行
- 检查页面状态
- 修改选择器
- 重新运行步骤

### 3. 查看追踪文件

```bash
npx playwright show-trace trace.zip
```

包含:
- 完整操作历史
- 网络请求
- 控制台日志
- DOM 快照

### 4. 增加日志

```typescript
// 添加详细日志
console.log('Step 1: Navigate to worklist');
console.log(`Current URL: ${page.url()}`);
console.log(`Element count: ${await page.locator('button').count()}`);
```

## 📚 更多资源

- [Playwright 官方文档](https://playwright.dev/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [测试最佳实践](https://playwright.dev/docs/best-practices)
- [CI/CD 集成指南](https://playwright.dev/docs/ci)

## 🤝 贡献指南

1. 创建功能分支
2. 添加测试用例
3. 确保所有测试通过
4. 提交 Pull Request
5. 等待 Code Review

## 📄 许可

本测试套件是 CMS Automation 项目的一部分。

---

**维护者**: CMS Automation Team
**最后更新**: 2025-11-09
**版本**: 1.0.0
