# Phase 7 E2E Tests

快速参考指南，用于运行Phase 7统一AI优化服务的E2E测试。

## 快速开始

### 1. 运行所有测试

```bash
# 测试本地环境
cd /home/kingofalbert/projects/CMS/frontend
./run-phase7-tests.sh local all

# 测试生产环境
./run-phase7-tests.sh prod all
```

### 2. 运行特定测试套件

```bash
# 优化生成测试 (7个测试)
./run-phase7-tests.sh local generation

# 内容质量测试 (5个测试)
./run-phase7-tests.sh local quality

# 监控测试 (5个测试)
./run-phase7-tests.sh local monitoring

# 错误处理测试 (3个测试)
./run-phase7-tests.sh local errors

# 性能基准测试 (2个测试)
./run-phase7-tests.sh local performance
```

## 前置条件

### 本地测试

**1. 启动后端服务:**
```bash
cd /home/kingofalbert/projects/CMS/backend
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**2. 启动前端服务 (可选):**
```bash
cd /home/kingofalbert/projects/CMS/frontend
npm run build
npm run preview
```

**3. 运行测试:**
```bash
./run-phase7-tests.sh local all
```

### 生产测试

```bash
./run-phase7-tests.sh prod all
```

## 测试文件

- **主测试:** `phase7-unified-optimization.spec.ts`
- **测试数量:** 22个测试用例
- **测试套件:** 6个

## 测试覆盖

✅ 统一优化生成 (单次API调用)
✅ 缓存机制验证
✅ 标题/SEO/FAQ内容质量
✅ 成本和性能监控
✅ 错误处理
✅ 性能基准测试

## 性能基准

| 指标 | 阈值 |
|-----|-----|
| 响应时间 | < 35秒 |
| 单次成本 | < $0.15 |
| Token效率 | > 30k tokens/$ |

## 手动运行

### 运行所有测试
```bash
TEST_LOCAL=1 npx playwright test phase7-unified-optimization
```

### 带UI运行
```bash
TEST_LOCAL=1 npx playwright test phase7-unified-optimization --ui
```

### 调试模式
```bash
TEST_LOCAL=1 npx playwright test phase7-unified-optimization --debug
```

### 查看报告
```bash
npx playwright show-report
```

## 故障排查

### Backend不可用
```bash
# 检查backend健康状态
curl http://localhost:8000/health

# 启动backend
cd backend && uvicorn src.main:app --port 8000
```

### Playwright未安装
```bash
npx playwright install chromium
```

### 测试超时
- 检查网络连接
- 检查Anthropic API状态
- 增加超时时间 (playwright.config.ts)

## 完整文档

详细文档请参考:
- `/backend/docs/phase7_e2e_testing_guide.md`
- `/backend/docs/phase7_unified_optimization_api_reference.md`

## 快速参考

```bash
# 本地 - 所有测试
./run-phase7-tests.sh local all

# 本地 - 快速测试（只测试生成）
./run-phase7-tests.sh local generation

# 生产 - 监控测试
./run-phase7-tests.sh prod monitoring

# 调试单个测试
TEST_LOCAL=1 npx playwright test -g "should generate all optimizations" --debug
```

---

**维护者:** CMS Automation Team
**最后更新:** 2025-01-08
