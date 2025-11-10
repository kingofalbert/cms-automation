# CMS Automation - E2E测试套件概览

## 📊 测试统计

| 指标 | 数值 |
|------|------|
| 总测试用例数 | 49 |
| 测试文件数 | 6 |
| 工具函数 | 20+ |
| 覆盖的页面 | 3 (Worklist, Review, Settings) |
| 测试类型 | 7 (功能、导航、性能、错误、视觉、可访问性、数据一致性) |

## 🗂️ 测试套件结构

```
frontend/e2e/
├── regression/                           # 回归测试套件
│   ├── README.md                         # 详细文档
│   ├── run-tests.sh                      # 测试运行脚本
│   ├── worklist.spec.ts                  # Worklist管理测试 (12个测试)
│   ├── proofreading-review.spec.ts       # 校对审核测试 (14个测试)
│   ├── settings.spec.ts                  # 设置页面测试 (9个测试)
│   ├── chrome-devtools-integration.spec.ts # DevTools集成测试 (7个测试)
│   └── complete-regression.spec.ts       # 完整回归套件 (7个测试)
│
├── utils/
│   └── test-helpers.ts                   # 测试工具函数库
│
└── TEST_SUITE_OVERVIEW.md               # 本文档
```

## 🎯 测试覆盖详情

### 1. Worklist管理测试 (`worklist.spec.ts`)

**目标**: 验证工作列表页面的所有功能

| 测试ID | 测试名称 | 描述 |
|--------|---------|------|
| WL-001 | 页面加载 | 验证Worklist页面成功加载 |
| WL-002 | 统计卡片 | 验证统计数据卡片正确显示 |
| WL-003 | 表格数据 | 验证表格加载并显示数据 |
| WL-004 | 搜索功能 | 测试搜索框过滤功能 |
| WL-005 | 状态筛选 | 测试状态筛选器 |
| WL-006 | Review按钮 | 验证Review按钮存在且可用 |
| WL-007 | 页面导航 | 测试导航到审核页面 |
| WL-008 | 语言选择器 | 验证语言切换功能 |
| WL-009 | 设置按钮 | 验证设置按钮可见 |
| WL-010 | 性能指标 | 测量页面加载性能 |
| WL-011 | 控制台错误 | 检测JavaScript错误 |
| WL-012 | 网络故障 | 检测网络请求失败 |

**关键特性**:
- ✅ 使用Chrome DevTools监控网络和控制台
- ✅ 性能基准测试
- ✅ 自动截图
- ✅ 错误检测和报告

### 2. 校对审核工作流测试 (`proofreading-review.spec.ts`)

**目标**: 验证校对审核页面的所有交互和功能

| 测试ID | 测试名称 | 描述 |
|--------|---------|------|
| PR-001 | 页面加载 | 验证审核页面加载 |
| PR-002 | 文章标题 | 验证文章标题显示 |
| PR-003 | 视图按钮 | 验证视图模式按钮存在 |
| PR-004 | 视图切换 | 测试视图模式切换功能 |
| PR-005 | 问题列表 | 验证问题列表显示 |
| PR-006 | 问题筛选 | 测试问题筛选功能 |
| PR-007 | 问题详情 | 验证问题详情面板 |
| PR-008 | 问题选择 | 测试问题选择交互 |
| PR-009 | 审核备注 | 测试审核备注输入 |
| PR-010 | 操作按钮 | 验证所有操作按钮 |
| PR-011 | AI优化卡片 | 验证AI优化建议显示 |
| PR-012 | 性能指标 | 测量审核页面性能 |
| PR-013 | Diff性能 | 测试Diff视图渲染性能 |
| PR-014 | 错误监控 | 交互过程中的错误监控 |

**关键特性**:
- ✅ 完整的视图模式测试 (Original, Rendered, Diff, Preview)
- ✅ 问题列表交互测试
- ✅ 性能敏感操作的专项测试
- ✅ 实时错误监控

### 3. 设置页面测试 (`settings.spec.ts`)

**目标**: 验证设置页面的配置和导航功能

| 测试ID | 测试名称 | 描述 |
|--------|---------|------|
| SET-001 | 页面加载 | 验证设置页面加载 |
| SET-002 | 页面标题 | 验证设置标题显示 |
| SET-003 | 配置区域 | 验证配置分区显示 |
| SET-004 | 表单输入 | 验证表单元素 |
| SET-005 | 保存按钮 | 验证保存按钮功能 |
| SET-006 | 返回按钮 | 验证返回/取消按钮 |
| SET-007 | 导航返回 | 测试返回到Worklist |
| SET-008 | 表单验证 | 测试表单验证逻辑 |
| SET-009 | 错误检查 | 检测控制台错误 |

**关键特性**:
- ✅ 表单元素验证
- ✅ 导航流程测试
- ✅ 配置持久化测试

### 4. Chrome DevTools集成测试 (`chrome-devtools-integration.spec.ts`)

**目标**: 使用Chrome DevTools进行高级监控和分析

| 测试ID | 测试名称 | 描述 |
|--------|---------|------|
| CDT-001 | 网络监控 | 监控并分析所有网络请求 |
| CDT-002 | 控制台检查 | 详细的控制台消息分析 |
| CDT-003 | 性能分析 | 完整的性能指标测量 |
| CDT-004 | 资源加载 | 分析资源加载和优化 |
| CDT-005 | 页面快照 | 捕获页面快照和截图 |
| CDT-006 | 元素检查 | DOM结构分析 |
| CDT-007 | 内存分析 | JavaScript堆内存使用分析 |

**关键特性**:
- ✅ 深度性能分析
- ✅ 资源优化建议
- ✅ 内存泄漏检测
- ✅ 网络瓶颈识别

### 5. 完整回归测试套件 (`complete-regression.spec.ts`)

**目标**: 端到端工作流验证

| 测试ID | 测试名称 | 描述 |
|--------|---------|------|
| REG-001 | 完整用户流程 | Worklist → Review完整流程 |
| REG-002 | 设置流程 | 设置页面完整流程 |
| REG-003 | 语言切换 | 多语言支持测试 |
| REG-004 | 性能基准 | 所有页面性能基准测试 |
| REG-005 | 错误恢复 | 测试应用错误恢复能力 |
| REG-006 | 可访问性 | 基本可访问性检查 |
| REG-007 | 数据一致性 | 跨页面数据一致性验证 |

**关键特性**:
- ✅ 真实用户场景模拟
- ✅ 多页面数据一致性
- ✅ 错误恢复能力测试
- ✅ 全面的性能基准

## 🛠️ 测试工具函数

### 核心工具 (`test-helpers.ts`)

#### 导航和等待
- `getTestConfig()`: 获取测试配置
- `navigateWithRetry()`: 带重试的页面导航
- `waitForPageReady()`: 等待页面完全加载
- `waitForElement()`: 等待元素出现
- `elementExists()`: 检查元素是否存在

#### 交互
- `clickWithRetry()`: 带重试的点击操作
- `fillInput()`: 填充表单输入
- `getTextContent()`: 获取文本内容

#### 监控
- `createConsoleMonitor()`: 创建控制台监控器
- `createNetworkMonitor()`: 创建网络监控器
- `measurePerformance()`: 测量性能指标

#### 断言
- `assertNoConsoleErrors()`: 断言无控制台错误
- `assertNoNetworkFailures()`: 断言无网络故障

#### 工具
- `takeScreenshot()`: 截图工具
- `waitForAPIResponse()`: 等待API响应

## 🚀 快速开始

### 安装和设置

```bash
cd frontend
npm install
npx playwright install chromium
```

### 运行测试

```bash
# 运行所有回归测试
./e2e/regression/run-tests.sh all

# 运行特定测试套件
./e2e/regression/run-tests.sh worklist
./e2e/regression/run-tests.sh proofreading
./e2e/regression/run-tests.sh settings
./e2e/regression/run-tests.sh devtools
./e2e/regression/run-tests.sh complete

# 快速冒烟测试
./e2e/regression/run-tests.sh smoke

# CI模式
./e2e/regression/run-tests.sh ci
```

### 高级选项

```bash
# 本地环境测试
./e2e/regression/run-tests.sh all --local

# 显示浏览器
./e2e/regression/run-tests.sh worklist --headed

# UI模式
./e2e/regression/run-tests.sh complete --ui

# 调试模式
./e2e/regression/run-tests.sh worklist --debug

# 自定义worker数
./e2e/regression/run-tests.sh all --workers=2

# 自定义重试次数
./e2e/regression/run-tests.sh all --retries=3
```

## 📊 测试报告

### 查看报告

```bash
# 查看HTML报告
npx playwright show-report

# 查看追踪文件
npx playwright show-trace test-results/trace.zip
```

### 报告内容

- ✅ 测试通过/失败统计
- ⏱️ 执行时间和性能指标
- 📸 自动截图 (成功和失败)
- 🎥 失败测试的视频录制
- 📋 详细的日志输出
- 🔍 网络请求追踪
- 📊 性能分析数据

## 📈 性能基准

### 页面加载时间目标

| 页面 | 首次内容绘制 (FCP) | 完全加载 |
|------|------------------|---------|
| Worklist | < 5s | < 15s |
| Review | < 8s | < 20s |
| Settings | < 5s | < 15s |

### 性能指标

测试会自动收集以下指标:
- Load Time (加载时间)
- DOM Content Loaded (DOM内容加载)
- First Contentful Paint (首次内容绘制)
- Time to Interactive (可交互时间)
- Total Size (总大小)
- Request Count (请求数量)

## 🔧 维护指南

### 添加新测试

1. 在相应的测试文件中添加测试用例
2. 使用描述性的测试ID (如 WL-XXX, PR-XXX)
3. 添加详细的console.log输出
4. 包含截图
5. 更新本文档

### 更新测试工具

修改 `utils/test-helpers.ts` 以添加新的工具函数。

### 调试失败的测试

```bash
# 1. 使用UI模式
npx playwright test --ui

# 2. 使用debug模式
npx playwright test --debug

# 3. 查看追踪
npx playwright show-trace test-results/trace.zip

# 4. 查看截图
open test-results/screenshots/
```

## 🤝 贡献

如果您想添加新的测试用例或改进现有测试:

1. Fork 项目
2. 创建功能分支
3. 编写测试
4. 确保所有测试通过
5. 提交Pull Request

## 📞 支持

如有问题或建议,请:
- 查阅 `e2e/regression/README.md` 详细文档
- 查看 [Playwright 文档](https://playwright.dev/)
- 联系团队维护者

---

**最后更新**: 2025-11-09
**维护者**: CMS Automation Team
**文档版本**: 1.0.0
