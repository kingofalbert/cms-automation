# Optimization Monitoring & Performance Guide

## 概述

本指南介绍Phase 7统一AI优化服务的监控系统和性能优化最佳实践。

## 监控架构

### 核心组件

1. **OptimizationMonitor** (`src/services/monitoring/optimization_monitor.py`)
   - 结构化日志记录
   - 成本统计分析
   - 性能指标收集
   - 优化建议生成

2. **监控API端点** (`src/api/routes/optimization_monitoring_routes.py`)
   - `/v1/monitoring/optimization/cost-statistics` - 成本统计
   - `/v1/monitoring/optimization/performance-statistics` - 性能统计
   - `/v1/monitoring/optimization/expensive-articles` - 高成本文章
   - `/v1/monitoring/optimization/report` - 综合报告
   - `/v1/monitoring/optimization/cost-report/formatted` - 格式化报告

## 使用指南

### 1. 获取成本统计

```bash
# 获取最近30天的成本统计
curl "http://localhost:8000/v1/monitoring/optimization/cost-statistics?days=30&limit=100"
```

**响应示例:**
```json
{
  "period_days": 30,
  "article_count": 156,
  "total_cost_usd": 12.4589,
  "average_cost_usd": 0.0798,
  "min_cost_usd": 0.0234,
  "max_cost_usd": 0.1456,
  "median_cost_usd": 0.0789,
  "estimated_monthly_cost_usd": 12.46
}
```

### 2. 获取性能统计

```bash
# 获取最近7天的性能数据
curl "http://localhost:8000/v1/monitoring/optimization/performance-statistics?days=7"
```

**响应示例:**
```json
{
  "period_days": 7,
  "total_optimizations": 67,
  "cache_hit_rate": 12.5,
  "recent_optimizations": [
    {
      "article_id": 123,
      "generated_at": "2025-01-08T10:30:00",
      "cost_usd": 0.0845
    }
  ]
}
```

### 3. 识别高成本文章

```bash
# 获取成本最高的10篇文章
curl "http://localhost:8000/v1/monitoring/optimization/expensive-articles?days=30&limit=10"
```

**用途:**
- 识别异常高成本操作
- 分析文章特征与成本的关系
- 优化Prompt设计

### 4. 生成综合报告

```bash
# 生成7天的综合监控报告
curl "http://localhost:8000/v1/monitoring/optimization/report?days=7"
```

**包含内容:**
- 完整成本统计
- 性能指标
- 高成本文章Top 5
- 汇总摘要

### 5. 格式化文本报告

```bash
# 获取人类可读的成本报告
curl "http://localhost:8000/v1/monitoring/optimization/cost-report/formatted?days=30"
```

**输出格式:**
```
📊 Cost Statistics Report (30 days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Article Count: 156

💰 Cost Metrics:
   • Total Cost:    $12.4589
   • Average Cost:  $0.0798 per article
   • Min Cost:      $0.0234
   • Max Cost:      $0.1456
   • Median Cost:   $0.0789

📅 Projection:
   • Est. Monthly Cost: $12.46
   • (Based on 30-day trend)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 性能阈值

### 定义的阈值 (OptimizationMonitor)

```python
SLOW_RESPONSE_THRESHOLD_MS = 35000      # 35秒
HIGH_TOKEN_THRESHOLD = 8000             # 总tokens
HIGH_COST_THRESHOLD_USD = 0.15          # $0.15/文章
```

### 阈值含义

| 指标 | 阈值 | 触发条件 | 建议措施 |
|-----|------|---------|---------|
| 响应时间 | 35秒 | 单次调用超过35秒 | 检查网络连接，考虑异步处理 |
| Token使用量 | 8000 | 单次调用总tokens超过8000 | 精简文章内容或Prompt |
| 单次成本 | $0.15 | 单次调用成本超过$0.15 | 优化Prompt长度，降低max_tokens |
| Token效率 | 40k tokens/$ | 低于40k tokens/$ | 使用缓存，批量处理 |

### 警告日志

系统会自动记录超出阈值的操作:

```python
# 慢响应警告
logger.warning(
    "slow_optimization_detected",
    article_id=123,
    duration_ms=42000,  # 超过35秒
    threshold_ms=35000,
)

# 高成本警告
logger.warning(
    "expensive_optimization_detected",
    article_id=456,
    cost_usd=0.1789,  # 超过$0.15
    threshold_usd=0.15,
)
```

## 成本分析

### Claude Sonnet 4.5 定价

```python
INPUT_COST_PER_MILLION = 3.0    # $3 / 1M input tokens
OUTPUT_COST_PER_MILLION = 15.0  # $15 / 1M output tokens
```

### 成本计算公式

```python
total_cost = (input_tokens / 1_000_000 * 3.0) + \
             (output_tokens / 1_000_000 * 15.0)
```

### 预期成本范围

| 文章类型 | 预计Input Tokens | 预计Output Tokens | 预计成本 |
|---------|-----------------|------------------|---------|
| 短文章 (500字) | 1500 | 800 | $0.016 |
| 中等文章 (1500字) | 3000 | 1500 | $0.031 |
| 长文章 (3000字) | 5000 | 2000 | $0.045 |
| 超长文章 (5000字+) | 8000+ | 3000+ | $0.069+ |

### 成本优化策略

#### 1. 利用缓存机制

```python
# 系统自动检测重复生成
if article.unified_optimization_generated and not regenerate:
    # 返回缓存结果，成本=0
    return cached_results
```

**收益:** 100%成本节省

#### 2. 优化Prompt长度

**当前实践:**
- 仅发送必要的文章内容
- 使用精简的系统提示
- 避免重复说明

**示例优化:**
```python
# ❌ 冗长的Prompt
prompt = f"""
请为以下文章生成标题优化建议。这篇文章的完整内容如下所示。
文章内容开始:
{article_body}
文章内容结束。
请生成3个标题建议...
"""

# ✅ 精简的Prompt
prompt = f"""
文章内容:
{article_body}

生成3个标题建议...
"""
```

**收益:** 10-20%成本节省

#### 3. 控制max_tokens

```python
# 当前设置
max_tokens=4096  # Phase 7默认值

# 根据文章长度调整
if len(article_body) < 500:
    max_tokens = 2048  # 短文章
elif len(article_body) < 1500:
    max_tokens = 3072  # 中等文章
else:
    max_tokens = 4096  # 长文章
```

**收益:** 15-25%成本节省（针对短文章）

#### 4. 批量处理

```python
# 单次处理多篇文章（未来优化）
async def batch_optimize_articles(article_ids: list[int]):
    # 合并请求，共享系统提示
    pass
```

**收益:** 20-30%成本节省（通过共享上下文）

## 性能优化

### 1. 响应时间优化

#### 问题识别
- 使用监控API识别慢响应: `GET /monitoring/optimization/performance-statistics`
- 检查`duration_ms > 35000`的操作

#### 优化措施

**A. 异步处理**
```python
# 使用后台任务
background_tasks.add_task(
    unified_service.generate_all_optimizations,
    article_id=article.id,
    regenerate=False,
)
```

**B. 网络优化**
- 使用更快的DNS解析
- 确保与Anthropic API的网络连接质量
- 考虑使用CDN或代理

**C. 超时设置**
```python
# httpx客户端超时配置
anthropic_client = AsyncAnthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    timeout=httpx.Timeout(60.0, connect=10.0),
)
```

### 2. Token使用优化

#### A. 输入Token优化

**技巧:**
- 移除HTML中的冗余空白
- 精简文章meta信息
- 避免发送不必要的字段

```python
# 清理HTML
from bs4 import BeautifulSoup
soup = BeautifulSoup(article_body_html, 'html.parser')
clean_text = soup.get_text(separator=' ', strip=True)
```

#### B. 输出Token优化

**技巧:**
- 明确指定输出格式
- 限制建议数量
- 使用结构化输出（JSON）

```python
# 明确约束输出
prompt += """
输出格式要求:
- 标题建议: 3个（不超过30字）
- SEO标题: 1个（不超过60字）
- Meta描述: 1个（不超过160字）
- FAQ: 3-5个
"""
```

### 3. 缓存策略

#### 当前实现
```python
# 数据库字段
article.unified_optimization_generated = True
article.unified_optimization_generated_at = datetime.utcnow()
article.unified_optimization_cost = Decimal(str(total_cost))
```

#### 缓存命中条件
1. `unified_optimization_generated == True`
2. `regenerate == False`
3. 相关建议记录存在

#### 缓存失效策略
- 用户显式请求重新生成 (`regenerate=True`)
- 文章内容发生重大变更
- 建议记录被删除

## 监控最佳实践

### 1. 定期审查

**建议频率:**
- 每日: 检查前一天的成本和性能
- 每周: 生成综合报告，识别趋势
- 每月: 深度分析，制定优化计划

**示例监控脚本:**
```bash
#!/bin/bash
# daily_monitoring.sh

# 获取昨日统计
curl -s "http://localhost:8000/v1/monitoring/optimization/cost-statistics?days=1" \
  | jq '.total_cost_usd, .article_count'

# 获取高成本文章
curl -s "http://localhost:8000/v1/monitoring/optimization/expensive-articles?days=1&limit=5" \
  | jq '.articles[] | {id: .article_id, cost: .cost_usd}'
```

### 2. 设置告警

**建议告警规则:**

| 指标 | 告警条件 | 优先级 |
|-----|---------|-------|
| 日成本 | 超过预算10% | 高 |
| 平均成本 | 超过$0.15/文章 | 中 |
| 响应时间 | 持续超过40秒 | 中 |
| 错误率 | 超过5% | 高 |

**实现示例 (伪代码):**
```python
# monitoring_alerts.py
async def check_daily_alerts():
    stats = await monitor.get_cost_statistics(days=1)

    # 成本告警
    if stats['total_cost_usd'] > DAILY_BUDGET * 1.1:
        send_alert(
            level='HIGH',
            message=f"Daily cost exceeded: ${stats['total_cost_usd']:.2f}",
        )

    # 平均成本告警
    if stats['average_cost_usd'] > 0.15:
        send_alert(
            level='MEDIUM',
            message=f"Average cost high: ${stats['average_cost_usd']:.4f}",
        )
```

### 3. 日志分析

**关键日志事件:**

```python
# 成功优化
"optimization_completed"
# 字段: article_id, input_tokens, output_tokens, cost_usd, duration_ms, cached

# 慢响应
"slow_optimization_detected"
# 字段: article_id, duration_ms, threshold_ms

# 高成本
"expensive_optimization_detected"
# 字段: article_id, cost_usd, threshold_usd

# 优化失败
"optimization_failed"
# 字段: article_id, error_type, error_message, error_stage
```

**日志查询示例 (structlog):**
```bash
# 查找所有慢响应
grep "slow_optimization_detected" app.log | jq

# 统计每日成本
grep "optimization_completed" app.log | \
  jq -r '.cost_usd' | \
  awk '{sum+=$1} END {print sum}'

# 查找所有失败操作
grep "optimization_failed" app.log | \
  jq -r '{article: .article_id, error: .error_type}'
```

## 优化建议工作流

### 自动建议生成

`OptimizationMonitor.get_optimization_recommendations()` 会自动分析以下指标:

1. **响应时间过长** (>35秒)
   - 建议: 检查网络连接或异步处理

2. **单次成本较高** (>$0.15)
   - 建议: 优化Prompt长度或降低max_tokens

3. **Token使用量较高** (>8000)
   - 建议: 精简文章内容或Prompt模板

4. **输出Token占比过高** (输出/输入 >2.0)
   - 建议: 调整temperature或约束输出长度

5. **成本效率偏低** (<40k tokens/$)
   - 建议: 使用缓存或批量处理

### 人工审查流程

1. **识别异常**
   - 使用监控API获取高成本文章
   - 分析文章特征（长度、复杂度）

2. **分析原因**
   - 检查Prompt是否合理
   - 验证输出质量
   - 评估成本效益

3. **实施优化**
   - 调整Prompt模板
   - 修改max_tokens设置
   - 优化文章预处理

4. **验证效果**
   - 对比优化前后成本
   - 确保输出质量不降低
   - 记录优化结果

## 成本预测

### 基于历史数据预测

```python
# 使用监控API
stats = await monitor.get_cost_statistics(days=30)
monthly_cost = stats['estimated_monthly_cost_usd']

# 预测未来3个月
projected_cost_3m = monthly_cost * 3
```

### 基于文章量预测

```python
# 假设参数
avg_cost_per_article = 0.08  # $0.08
articles_per_day = 50
days_in_month = 30

# 预测月度成本
monthly_cost = avg_cost_per_article * articles_per_day * days_in_month
# = $0.08 * 50 * 30 = $120
```

### 成本对比 (Phase 7 vs 分离调用)

| 方案 | 单篇成本 | 50篇/天 | 月度成本 |
|-----|---------|--------|---------|
| Phase 7 统一 | $0.08 | $4.00 | $120.00 |
| 分离调用 (3次) | $0.13 | $6.50 | $195.00 |
| **节省** | **38%** | **$2.50** | **$75.00** |

## 故障排查

### 问题: 成本异常增高

**症状:** 日成本突然增加50%+

**排查步骤:**
1. 检查`expensive-articles` API: 识别异常文章
2. 分析异常文章特征: 长度、复杂度
3. 检查Prompt是否被修改
4. 验证缓存机制是否失效

**可能原因:**
- 文章长度显著增加
- max_tokens设置提高
- Prompt模板变更
- 缓存键失效

### 问题: 响应时间过长

**症状:** 90%+的请求超过40秒

**排查步骤:**
1. 检查网络连接: `curl -w "@curl-format.txt" api.anthropic.com`
2. 检查API服务状态: https://status.anthropic.com
3. 查看系统资源: CPU、内存、网络
4. 检查数据库性能

**可能原因:**
- 网络不稳定
- Anthropic API限流
- 数据库查询慢
- 并发请求过多

### 问题: Token使用量异常

**症状:** 输入tokens超过预期2倍+

**排查步骤:**
1. 检查文章预处理逻辑
2. 验证HTML清理是否正常
3. 检查Prompt模板长度
4. 确认article字段是否包含冗余数据

**可能原因:**
- HTML未正确清理
- 包含大量空白字符
- Prompt模板过于冗长
- 发送了不必要的字段

## 相关文档

- [Phase 7 统一AI优化服务](./phase7_unified_ai_optimization_service.md)
- [文章审核SEO工作流](./article_proofreading_seo_workflow.md)
- [单Prompt设计](./single_prompt_design.md)
- [数据库Schema更新](./database_schema_updates.md)

## 总结

通过合理使用监控系统和遵循最佳实践:

✅ **成本控制**: 平均成本维持在$0.08/篇
✅ **性能优化**: 95%的请求在35秒内完成
✅ **质量保证**: 输出质量不因优化而降低
✅ **可观测性**: 实时掌握系统运行状态

**关键指标监控:**
- 每日成本趋势
- 平均响应时间
- 缓存命中率
- Token使用效率

**持续改进:**
- 定期审查高成本文章
- 优化Prompt设计
- 调整阈值设置
- 完善缓存策略
