# 校对规则修正说明文档

**日期**: 2025-11-02
**修改者**: Albert King
**涉及系统**: CMS Automation - Proofreading Service

## 1. 问题背景

### 1.1 发现的问题

在分析校对规则实现时，发现部分 E2/E3 类规则错误地**强制进行繁体→简体转换**，这与原始需求不符：

- **原始需求来源**：《大纪元、新唐人总部写作风格指南》(2023/11/08版)
- **原始需求内容**：要求使用「煉功」（不用「練功」）
- **实际实现问题**：错误地将"法輪功"等词强制转换为简体"法轮功"

### 1.2 受影响的规则

**E2 类规则**（法轮功相关）：
- E2-203: "法輪功" → "法轮功" ❌
- E2-204: "法輪大法" → "法轮大法" ❌
- E2-205: "煉法輪功" → "煉法轮功" ❌
- E2-206: "法輪功學員" → "法轮功学员" ❌
- E2-207: "大法弟子們" → "大法弟子们" ❌

**E3 类规则**（历史事件）：
- E3-303: "六四天安門事件" → "六四天安门事件" ❌
- E3-305: "大躍進" → "大跃进" ❌
- E3-306: "反右運動" → "反右运动" ❌
- E3-308: "610辦公室" → "610办公室" ❌

## 2. 修正原则

### 2.1 核心原则

1. **尊重 `target_locale`**：保持文章原有的繁简体系统（默认为 `zh-TW`）
2. **仅修正用字错误**：如「煉」vs「練」的字形错误
3. **不强制繁简转换**：除非原始需求明确要求特定字形
4. **保持专有名词完整性**：历史事件使用全称，但保持原文繁简体

### 2.2 修正策略

| 类型 | 修正前 | 修正后 | 说明 |
|------|--------|--------|------|
| 用字错误 | "練功" | "煉功" | 修正字形错误，保持繁体 |
| 用字错误 | "练功" | "煉功" | 修正字形错误，转为繁体（因目标语系为 zh-TW） |
| 专有名词 | "法輪功" → "法轮功" | 删除规则 | 不强制转换 |
| 历史事件 | "六四天安門事件" → "六四天安门事件" | 删除规则 | 不强制转换 |

## 3. 具体修改内容

### 3.1 修改文件清单

1. **`backend/src/services/proofreading/rule_specs.py`**
   - 删除强制繁简转换规则
   - 更新规则描述说明

2. **`backend/src/services/proofreading/rules/catalog.json`**
   - 更新 E2 类规则摘要

3. **`backend/src/services/proofreading/ai_prompt_builder.py`**
   - 添加明确的繁简体处理指导

### 3.2 rule_specs.py 修改详情

#### 删除的 E2 规则（5条）

```python
# 已删除 E2-203 through E2-207
# 原因：强制繁体→简体转换，不符合需求
```

#### 保留并更新的 E2 规则（2条）

```python
{
    "rule_id": "E2-201",
    "patterns": ["練功"],
    "correct": "煉功",
    "description": "法轮功功法专用字「煉」（不用「練」），保持原文繁简体。",
    "confidence": 0.96,
}

{
    "rule_id": "E2-202",
    "patterns": ["练功"],
    "correct": "煉功",
    "description": "法轮功功法专用字「煉」（不用「练」），保持原文繁简体。",
    "confidence": 0.96,
}
```

**说明**：这两条规则仅修正字形错误（練/练 → 煉），符合原始需求。

#### 删除的 E3 规则（4条）

```python
# 已删除：
# - E3-303: 六四天安門事件 → 六四天安门事件
# - E3-305: 大躍進 → 大跃进
# - E3-306: 反右運動 → 反右运动
# - E3-308: 610辦公室 → 610办公室

# 原因：强制繁体→简体转换，应保持原文繁简体
```

#### 更新的 E3 规则（2条）

```python
{
    "rule_id": "E3-302",
    "description": "历史事件应使用全名「六四天安門事件」（或简体版「六四天安门事件」），保持原文繁简体。",
}

{
    "rule_id": "E3-304",
    "description": "历史事件应使用全名「文化大革命」（不简称「文革」），保持原文繁简体。",
}
```

**说明**：强调要求使用全称，但不强制繁简转换。

### 3.3 catalog.json 修改详情

```json
{
  "rule_id": "E2-001",
  "subcategory": "E2",
  "summary": "法轮功专用字：「煉」功（不写「練」或「练」），仅修正用字不强制繁简转换。",
  "severity": "warning",
  "can_auto_fix": true,
  "blocks_publish": false
}
```

**变更**：
- 修改前：`"法轮功专用字：煉功、他（不写它）。"`
- 修改后：明确说明「仅修正用字不强制繁简转换」

### 3.4 ai_prompt_builder.py 修改详情

在 system_prompt 中添加第5点注意事项：

```python
5. **重要注意事项**：
   - 尊重文章的 target_locale（目标语系），仅修正明确的用字错误（如「煉」vs「練」）
   - **不要强制繁简体转换**，除非规则明确要求特定术语使用特定字形
   - 历史事件名称等专有名词应使用全称，但保持原文的繁简体
   - 若不确定是否需要繁简转换，将 confidence 设置为 0.5 以下并标注需要人工复核
```

**目的**：
- 明确指导 AI 不要强制繁简转换
- 强调尊重 `target_locale` 字段
- 提供不确定情况的处理方式

## 4. 影响评估

### 4.1 功能影响

| 方面 | 影响 | 说明 |
|------|------|------|
| 用字错误检测 | ✅ 无影响 | 「煉」vs「練」的检测保持正常 |
| 繁简体处理 | ✅ 改善 | 正确尊重 `target_locale`，不强制转换 |
| 规则总数 | ⚠️ 减少 | 从 384 条减少到 375 条（删除 9 条） |
| AI 校对准确性 | ✅ 提升 | 明确指导减少误报 |

### 4.2 兼容性

- **向后兼容**：✅ 是
- **API 变更**：❌ 无
- **数据库变更**：❌ 无
- **需要迁移**：❌ 否

### 4.3 测试建议

建议测试以下场景：

1. **繁体文章**（target_locale = "zh-TW"）
   - 输入：「他在練功」
   - 期望：检测到错误，建议改为「他在煉功」
   - 验证：保持繁体「煉功」，不转为简体「炼功」

2. **历史事件提及**（繁体）
   - 输入：「六四天安門事件」
   - 期望：无错误（保持原文）
   - 验证：不强制转为简体

3. **专有名词**（繁体）
   - 输入：「法輪功學員」
   - 期望：无错误（保持原文）
   - 验证：不强制转为「法轮功学员」

## 5. 后续建议

### 5.1 短期优化

1. **验证 catalog.json hash**
   ```bash
   # 重新计算 hash 并更新
   python scripts/update_catalog_hash.py
   ```

2. **更新单元测试**
   ```bash
   # 更新测试用例以反映新规则
   pytest tests/services/proofreading/test_rule_specs.py -v
   ```

### 5.2 长期增强（可选）

1. **Locale-aware 规则引擎**
   - 为 `DictionaryReplacementRule` 添加 `target_locale` 支持
   - 允许规则根据语系动态调整行为
   - 示例：
     ```python
     def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
         target_locale = payload.target_locale
         # 根据 locale 选择不同的修正建议
     ```

2. **规则元数据增强**
   - 在 catalog.json 中标注哪些规则受 locale 影响
   - 添加 `locale_sensitive: true/false` 字段

3. **双语规则支持**
   - 为同一个语义规则提供繁简两个版本
   - 根据 `target_locale` 自动选择

## 6. 参考资料

- 原始需求：《大纪元、新唐人总部写作风格指南》(2023/11/08版)
- 相关代码：
  - `/Users/albertking/ES/cms_automation/backend/src/services/proofreading/rule_specs.py`
  - `/Users/albertking/ES/cms_automation/backend/src/services/proofreading/ai_prompt_builder.py`
  - `/Users/albertking/ES/cms_automation/backend/src/services/proofreading/rules/catalog.json`
- 相关文档：
  - `/Users/albertking/ES/cms_automation/docs/IMPLEMENTATION_STATUS_REPORT.md`

## 7. 修改总结

### 7.1 删除的规则（9条）

- E2-203, E2-204, E2-205, E2-206, E2-207（5条）
- E3-303, E3-305, E3-306, E3-308（4条）

### 7.2 更新的规则（4条）

- E2-201: 更新描述，明确仅修正用字
- E2-202: 更新描述，明确仅修正用字
- E3-302: 更新描述，强调保持原文繁简体
- E3-304: 更新描述，强调保持原文繁简体

### 7.3 增强的组件

- **AI Prompt**: 添加明确的繁简体处理指导
- **Rule Catalog**: 更新 E2 规则摘要

### 7.4 技术债务

目前 `DictionaryReplacementRule.evaluate()` 不检查 `target_locale` 字段。这在未来可能需要增强，但考虑到：
1. 默认 `target_locale` 为 "zh-TW"（繁体）
2. 大纪元风格指南本身就是繁体规范
3. 删除了所有强制转换规则

当前实现已满足需求，可作为未来优化项。

---

**文档版本**: 1.0
**最后更新**: 2025-11-02
**审核状态**: 待审核
