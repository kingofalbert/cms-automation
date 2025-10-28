# WordPress 集成测试

本目录包含与真实 WordPress 环境交互的集成测试。

## 前置条件

### 1. 启动 WordPress 测试环境

```bash
# 启动 Docker 容器
docker compose -f docker-compose.test.yml up -d

# 等待初始化完成（约 1-2 分钟）
docker compose -f docker-compose.test.yml logs -f wp-cli

# 看到 "✓ 初始化完成！可以开始测试了。" 后按 Ctrl+C 退出日志查看
```

### 2. 验证 WordPress 可访问

访问 http://localhost:8001/wp-admin

- 用户名: `admin`
- 密码: `password`

如果能成功登录，说明测试环境已准备好。

## 运行测试

### 运行所有集成测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行所有集成测试
pytest tests/integration/ -v -m integration
```

### 运行特定测试

```bash
# 只运行选择器验证测试
pytest tests/integration/test_wordpress_integration.py::TestSelectorValidation -v

# 只运行性能测试
pytest tests/integration/ -v -m performance

# 运行完整工作流测试
pytest tests/integration/test_wordpress_integration.py::TestWordPressIntegration::test_08_full_workflow -v

# 跳过慢速测试
pytest tests/integration/ -v -m "integration and not slow"
```

### 运行带详细日志的测试

```bash
# 显示打印输出
pytest tests/integration/ -v -s

# 显示日志输出
pytest tests/integration/ -v --log-cli-level=INFO
```

## 测试说明

### TestWordPressIntegration

核心集成测试类，包含：

1. **test_01_login_success** - 验证登录功能
2. **test_02_login_failure_wrong_password** - 验证登录失败处理
3. **test_03_create_article_basic** - 验证创建文章
4. **test_04_configure_seo** - 验证 SEO 配置
5. **test_05_upload_image** - 验证图片上传
6. **test_06_set_featured_image** - 验证特色图片设置
7. **test_07_publish_article** - 验证文章发布
8. **test_08_full_workflow** - 验证完整工作流（标记为 slow）

### TestSelectorValidation

选择器验证测试，确保所有 CSS 选择器在实际 WordPress 中有效：

- **test_validate_login_selectors** - 验证登录页面选择器
- **test_validate_editor_selectors** - 验证编辑器选择器

### TestPerformance

性能测试，验证系统性能指标：

- **test_publish_within_target_time** - 验证发布时间 < 180 秒

## 测试标记 (Markers)

- `@pytest.mark.integration` - 标记为集成测试
- `@pytest.mark.validator` - 标记为选择器验证测试
- `@pytest.mark.performance` - 标记为性能测试
- `@pytest.mark.slow` - 标记为慢速测试

## 故障排除

### 测试失败：连接被拒绝

**问题**: `ConnectionRefusedError` 或无法连接到 WordPress

**解决方案**:
```bash
# 检查 WordPress 容器是否运行
docker compose -f docker-compose.test.yml ps

# 如果没有运行，启动它
docker compose -f docker-compose.test.yml up -d

# 等待初始化完成
docker compose -f docker-compose.test.yml logs -f wp-cli
```

### 测试失败：选择器无效

**问题**: 选择器验证测试失败

**解决方案**:
1. 手动访问 http://localhost:8001/wp-admin
2. 使用浏览器开发者工具检查元素
3. 更新 `config/selectors.yaml` 中的选择器
4. 重新运行测试

### 测试失败：超时

**问题**: 测试在等待某个操作时超时

**解决方案**:
1. 增加超时时间（在 `src/config/loader.py` 中调整 `playwright_timeout`）
2. 检查 WordPress 是否响应缓慢
3. 查看 Docker 容器日志: `docker compose -f docker-compose.test.yml logs wordpress`

### 清理测试数据

```bash
# 删除测试文章（如果需要）
docker exec cms_test_wordpress \
  wp post delete $(wp post list --post_type=post --format=ids --allow-root) \
  --force --allow-root

# 重置整个 WordPress 环境
docker compose -f docker-compose.test.yml down -v
docker compose -f docker-compose.test.yml up -d
```

## 持续集成

### GitHub Actions 示例

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -r requirements.txt

      - name: Start WordPress Test Environment
        run: |
          docker compose -f docker-compose.test.yml up -d
          sleep 120  # 等待初始化

      - name: Run Integration Tests
        run: |
          source .venv/bin/activate
          pytest tests/integration/ -v -m integration

      - name: Cleanup
        if: always()
        run: docker compose -f docker-compose.test.yml down -v
```

## 性能基准

根据规格要求，完整文章发布流程应在 **180 秒**内完成。

当前性能目标：
- 登录: < 10 秒
- 创建文章: < 20 秒
- 上传图片: < 30 秒
- 配置 SEO: < 10 秒
- 发布: < 10 秒
- **总计**: < 180 秒

## 相关文档

- [测试环境使用指南](../README_TESTING.md)
- [WordPress Publishing Plan](../../specs/001-cms-automation/wordpress-publishing-plan.md)
- [选择器配置](../../config/selectors.yaml)
