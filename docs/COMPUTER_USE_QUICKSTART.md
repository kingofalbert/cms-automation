# Computer Use MVP 快速入门指南

## 🚀 快速开始

### 1. 环境准备

#### 必需的环境变量

在 `.env` 文件中配置：

```bash
# Anthropic API
ANTHROPIC_API_KEY=your-api-key-here

# 生产环境 WordPress
PROD_WORDPRESS_URL=https://admin.epochtimes.com
PROD_USERNAME=your-username
PROD_PASSWORD=your-password

# 如果有 HTTP Basic Auth
PROD_FIRST_LAYER_USERNAME=djy
PROD_FIRST_LAYER_PASSWORD=djy2013
```

#### 系统要求

- Python 3.10+
- 中文字体（可选，改善截图）
- 网络连接

### 2. 一键部署

```bash
# 克隆仓库
cd /path/to/CMS

# 运行部署脚本
./scripts/deploy_mvp.sh
```

### 3. 运行示例

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行交互式演示
python examples/computer_use_demo.py
```

---

## 📚 基本用法

### 使用 Computer Use Provider

```python
from src.providers.computer_use_provider import ComputerUseProvider
from src.config.computer_use_loader import load_instruction_templates
from src.models import WordPressCredentials

# 1. 加载指令模板
instructions = load_instruction_templates()

# 2. 创建 Provider
provider = ComputerUseProvider(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    instructions=instructions
)

# 3. 初始化
await provider.initialize()

# 4. 登录
credentials = WordPressCredentials(
    username=os.getenv('PROD_USERNAME'),
    password=os.getenv('PROD_PASSWORD')
)

await provider.login(
    wordpress_url=os.getenv('PROD_WORDPRESS_URL'),
    credentials=credentials
)

# 5. 创建文章
await provider.create_article(article, metadata)

# 6. 发布
await provider.publish(metadata)

# 7. 清理
await provider.cleanup()
```

---

## ⚙️ 高级配置

### 自定义重试策略

```python
from src.utils.retry import RetryConfig

provider = ComputerUseProvider(
    api_key=api_key,
    instructions=instructions,
    retry_config=RetryConfig(
        max_retries=5,
        initial_delay=3.0,
        max_delay=60.0
    )
)
```

### Token 预算管理

```python
from src.utils.token_manager import TokenBudget

provider.token_manager.budget = TokenBudget(
    per_session_limit=50_000,
    per_operation_limit=5_000,
    warning_threshold=0.7
)
```

---

## 📊 Token 成本

### 定价（Claude 3.5 Sonnet）

- Input: $3 / 1M tokens
- Output: $15 / 1M tokens

### 预估成本

| 操作 | Tokens | 成本 |
|------|--------|------|
| 登录 | ~1,500 | $0.03 |
| 创建文章 | ~3,000 | $0.06 |
| 上传图片 | ~2,000/张 | $0.04/张 |
| SEO 配置 | ~1,000 | $0.02 |
| 发布 | ~500 | $0.01 |
| **完整流程** | **~10,000** | **$0.20** |

---

## 🔧 故障排查

### 问题 1: API Key 无效

**症状**: `AuthenticationError`

**解决**:
```bash
# 检查 API Key
echo $ANTHROPIC_API_KEY

# 重新设置
export ANTHROPIC_API_KEY='your-key'
```

### 问题 2: 指令模板加载失败

**症状**: `FileNotFoundError: Instruction template not found`

**解决**:
```bash
# 验证文件存在
ls config/computer_use_instructions.yaml

# 手动测试
python src/config/computer_use_loader.py
```

### 问题 3: Token 使用过高

**症状**: 成本超出预期

**解决**:
- 查看 Token 使用报告
- 优化指令长度
- 增加缓存
- 减少重试次数

---

## 📈 监控与优化

### 查看 Token 使用报告

Provider 在 `cleanup()` 时自动生成报告：

```
============================================================
Token 使用报告
============================================================

📊 会话概览:
  运行时长: 120.5 秒
  总 Token 数: 15,234
  总成本: $0.2845
  预算使用率: 15.2%
  预计日成本: $204.25

📈 操作统计:
  api_call:
    调用次数: 18
    总 Token 数: 15,234
    平均 Token/次: 846
    总成本: $0.2845

💡 优化建议:
  ✅ Token 使用合理，无需优化
============================================================
```

### 优化建议

1. **减少API调用次数**: 批量操作
2. **优化指令长度**: 精简描述
3. **使用缓存**: 避免重复操作
4. **合理设置重试**: 平衡可靠性与成本

---

## 🎯 下一步

### Phase 2: Playwright 混合优化

完成 MVP 验证后，实施 Phase 2：

1. 实现 Playwright Provider
2. 添加混合架构
3. 实现智能降级
4. 成本优化（降低 80-90%）

预期效果：
- 成本: $0.02/文章（↓90%）
- 速度: 1.5-3分钟（↑50%）
- 可靠性: 98%（↑3%）

---

## 📞 获取帮助

- 查看日志: `logs/`
- 运行测试: `pytest tests/ -v`
- 查看示例: `examples/computer_use_demo.py`
- 文档: `docs/`
